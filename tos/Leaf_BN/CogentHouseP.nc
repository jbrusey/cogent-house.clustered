// -*- c -*-

module CogentHouseP
{
  uses {
    //low-level stuff
    interface Timer<TMilli> as SenseTimer;
    interface Timer<TMilli> as BlinkTimer;
    interface Timer<TMilli> as SendTimeOutTimer;
    interface Leds;
    interface Boot;
    
    //radio
    interface SplitControl as RadioControl;

    //ctp
    interface StdControl as CollectionControl;
    interface CtpInfo;

    // dissemination
    interface StdControl as DisseminationControl;
    interface DisseminationValue<AckMsg> as AckValue;
    interface Crc as CRCCalc ;
		
    //sending interfaces
    interface Send as StateSender;

    //SI Sensing
    interface Read<float *> as ReadTemp;
    interface TransmissionControl as TempTrans;
    interface Read<float *> as ReadHum;
    interface TransmissionControl as HumTrans;
    interface Read<float *> as ReadCO2;
    interface TransmissionControl as CO2Trans;
    interface Read<float> as ReadVolt;
    interface Read<float> as ReadVOC;
    interface Read<float> as ReadAQ;

    //Bitmask and packstate
    interface AccessibleBitVector as Configured;
    interface BitVector as ExpectReadDone;
    interface PackState;

    //Time
    interface LocalTime<TMilli>;
  }
}
implementation
{
  float last_duty = 0.;

  float last_errno = 1.;
  float last_transmitted_errno;

  uint32_t send_start_time;  
  uint32_t sense_start_time;
  bool phase_two_sensing = FALSE;
	
  ConfigMsg settings;
  ConfigPerType * ONE my_settings;

  /* default node type is determined by top 4 bits of node_id */
  uint8_t nodeType;

  bool sending;

  bool packet_pending = FALSE;

  message_t dataMsg;
  uint16_t message_size;
  uint8_t msgSeq = 0;
  uint8_t expSeq = 0;
  bool toSend = 0;

  int periodsToHeartbeat=HEARTBEAT_PERIOD;
  struct nodeType nt;
	

  /** reportError records a code to be sent on the next transmission. 
   * @param errno error code
   */
  void reportError(uint8_t errno) {
#ifdef DEBUG
    printf("Error message: %u\n", errno);
    printfflush();
#endif
    last_errno *= errno;
  }


  ////////////////////////////////////////////////////////////
  //sending methods


  void sendState()
  {
    packed_state_t ps;
    BNMsg *newData;
    int pslen;
    int i;
    am_addr_t parent;
#ifdef DEBUG
    printf("sendState %lu\n", call LocalTime.get());
    printfflush();
#endif
    if (sending) {
      reportError(ERR_SEND_WHILE_SENDING);
      return;
    }
    if (packet_pending) {
      reportError(ERR_SEND_WHILE_PACKET_PENDING);
      return;
    }

    if (periodsToHeartbeat<=0)
      call PackState.add(SC_HEARTBEAT, 1);

    if (call Configured.get(RS_DUTY))
      call PackState.add(SC_DUTY_TIME, last_duty);
    if (last_errno != 1.)
      call PackState.add(SC_ERRNO, last_errno);

    last_transmitted_errno = last_errno;
    pslen = call PackState.pack(&ps);
		
    message_size = sizeof (StateMsg) - (SC_SIZE - pslen) * sizeof (float);
    newData = call StateSender.getPayload(&dataMsg, message_size);
    if (newData != NULL) { 
      //we're going do a send so pack the msg count and then increment
      newData->timestamp = call LocalTime.get();
      newData->special = 0xc7;

      //increment and pack seq
      expSeq = msgSeq;
      msgSeq++;
      newData->seq = expSeq;

      newData->ctp_parent_id = -1;
      if (call CtpInfo.getParent(&parent) == SUCCESS) { 
	newData->ctp_parent_id = parent;
      }
     
      for (i = 0; i < sizeof newData->packed_state_mask; i++) { 
	newData->packed_state_mask[i] = ps.mask[i];
      }
      for (i = 0; i < pslen; i++) {
	newData->packed_state[i] = ps.p[i];
      }
      send_start_time = call LocalTime.get();
      call SendTimeOutTimer.startOneShot(LEAF_TIMEOUT_TIME);
      if (call StateSender.send(&dataMsg, message_size) == SUCCESS) {
#ifdef DEBUG
	  printf("sending begun at %lu\n", call LocalTime.get());
	  printfflush();
#endif
	sending = TRUE;
      }
    }
  }	
  
  ////////////////////////////////////////////////////////////
	
  event void Boot.booted() {
    // initial config
#ifdef DEBUG
    printf("Booted %lu\n", call LocalTime.get());
    printfflush();
#endif

    if (CLUSTER_HEAD)
      call RadioControl.start();

    nodeType = TOS_NODE_ID >> 12;
    my_settings = &settings.byType[nodeType];
    my_settings->samplePeriod = DEF_SENSE_PERIOD;
    my_settings->blink = FALSE;
		
    call Configured.clearAll();
    if (nodeType == 0) { 
      call Configured.set(RS_TEMPERATURE);
      call Configured.set(RS_HUMIDITY);
      call Configured.set(RS_VOLTAGE);
      call Configured.set(RS_DUTY);
    }
    else if (nodeType == 2) { /* co2 */
      call Configured.set(RS_TEMPERATURE);
      call Configured.set(RS_HUMIDITY);
      call Configured.set(RS_CO2);
      call Configured.set(RS_DUTY);
    }
    else if (nodeType == 3) { /* air quality */
      call Configured.set(RS_TEMPERATURE);
      call Configured.set(RS_HUMIDITY);
      call Configured.set(RS_CO2);
      call Configured.set(RS_AQ);
      call Configured.set(RS_VOC);
      call Configured.set(RS_DUTY);
    }
    
    call BlinkTimer.startOneShot(512L); /* start blinking to show that we are up and running */

    sending = FALSE;
    call SenseTimer.startOneShot(DEF_FIRST_PERIOD);
  }

  /** Restart the sense timer as a one shot. Using a one shot here
      rather than periodic removes the possibility of re-entering the
      sense loop before the last one has finished. The only slight
      problem here is that this may induce a slight drift in when the
      timer fires.

      This method is called both when the send completes (sendDone)
      and when the send times out.
   */
  void restartSenseTimer() {
    uint32_t stop_time = call LocalTime.get();
    uint32_t send_time, next_interval;
    sending = FALSE;

#ifdef DEBUG
    printf("restartSenseTimer at %lu\n", call LocalTime.get());
    printfflush();
#endif

    //Calculate the next interval
    if (stop_time < sense_start_time) // deal with overflow
      send_time = ((UINT32_MAX - sense_start_time) + stop_time + 1);
    else
      send_time = (stop_time - sense_start_time);
    
    if (my_settings->samplePeriod < send_time)
      next_interval = 0;
    else
      next_interval = my_settings->samplePeriod - send_time;

#ifdef DEBUG
    printf("startOneShot at %lu\n", call LocalTime.get());
    printf("interval of %lu\n", next_interval);
    printfflush();
#endif
    call SenseTimer.startOneShot(next_interval);

    if (my_settings->blink)
      call Leds.led1Off();
  }

  task void phaseTwoSensing();

  /* checkDataGathered
   * - only transmit data once all sensors have been read
   */
  task void checkDataGathered() {
    bool allDone = TRUE;
    uint8_t i;

    for (i = 0; i < RS_SIZE; i++) {
      if (call ExpectReadDone.get(i)) {
	allDone = FALSE;
	break;
      }
    }

    if (allDone) {
      if (phase_two_sensing) {
#ifdef DEBUG
	printf("allDone %lu\n", call LocalTime.get());
	printf("toSend %u\n", (int)toSend);
	printfflush();
#endif	
	if (toSend){
          if (!CLUSTER_HEAD)
	    call RadioControl.start();
          else
            sendState();
	}
	else
	  restartSenseTimer();
      }
      else { /* phase one complete - start phase two */
	phase_two_sensing = TRUE;
	post phaseTwoSensing();
      }
    }
  }

  /* SenseTimer.fired
   *
   * - begin sensing cycle by requesting, in parallel, for all active
       sensors to start reading.
  */
  event void SenseTimer.fired() {
    int i;

    //starting reads decrease periods To Heartbeat
    periodsToHeartbeat=periodsToHeartbeat-1;
    toSend=FALSE;
    sense_start_time = call LocalTime.get();
#ifdef BLINKY
    call Leds.led0Toggle();
#endif

    if (! sending) { 
#ifdef DEBUG
      printf("\n\nsensing begun at %lu\n", sense_start_time);
      printf("periodsToHeartbeat %u\n", periodsToHeartbeat);
      printfflush();
#endif
      call ExpectReadDone.clearAll();
      call PackState.clear();
      phase_two_sensing = FALSE;

      // only include phase one sensing here
      for (i = 0; i < RS_SIZE; i++) { 
	if (call Configured.get(i)) {
	  call ExpectReadDone.set(i);
	  if (i == RS_TEMPERATURE)
	    call ReadTemp.read();
	  else if (i == RS_HUMIDITY)
	    call ReadHum.read();
	  else if (i == RS_VOLTAGE)
	    call ReadVolt.read();
	  else
	    call ExpectReadDone.clear(i);
	}
      }
      /* it could be that no sensors are active but we still need to
	 send a packet (e.g. for duty cycle info)
      */
      post checkDataGathered();

    }
  }

  /* perform any phase two sensing */
  task void phaseTwoSensing() {
    int i;
    for (i = 0; i < RS_SIZE; i++) { 
      if (call Configured.get(i)) {
	call ExpectReadDone.set(i);
	if (i == RS_CO2)
	  call ReadCO2.read();
	else if (i == RS_AQ)
	  call ReadAQ.read();
	else if (i == RS_VOC)
	  call ReadVOC.read();
	else
	  call ExpectReadDone.clear(i);
      }
    }
    post checkDataGathered();
  }


  void do_readDone(error_t result, float data, uint raw_sensor, uint state_code) 
  {
    if (result == SUCCESS || periodsToHeartbeat<=0)
      call PackState.add(state_code, data);
    call ExpectReadDone.clear(raw_sensor);
    post checkDataGathered();
  }

  void do_readDone_BN(error_t result, float* data,  uint raw_sensor,  uint state_count, uint state_first){
    int i;

    for(i = 0; i < state_count; i++){
      call PackState.add(state_first+i,data[i]);
    }

    if (result == SUCCESS || periodsToHeartbeat<=0){
      toSend=TRUE;
    }
    call ExpectReadDone.clear(raw_sensor);
    post checkDataGathered();
  }

  event void ReadTemp.readDone(error_t result, float* data) {
    do_readDone_BN(result, data, RS_TEMPERATURE, SC_TEMP_COUNT, SC_TEMP_FIRST);
  }
	
  event void ReadHum.readDone(error_t result, float* data) {
    do_readDone_BN(result, data, RS_HUMIDITY, SC_HUM_COUNT, SC_HUM_FIRST);
  }    

  event void ReadCO2.readDone(error_t result, float* data) {
    do_readDone_BN(result, data, RS_CO2, SC_CO2_COUNT, SC_CO2_FIRST);
  }
   
  event void ReadAQ.readDone(error_t result, float data) {
    do_readDone(result, data, RS_AQ, SC_AQ);
  }
  
  event void ReadVOC.readDone(error_t result, float data) {	
    do_readDone(result, data, RS_VOC, SC_VOC);
  }

  event void ReadVolt.readDone(error_t result, float data) {
    do_readDone(result,(data), RS_VOLTAGE, SC_VOLTAGE);
  }

  event void RadioControl.startDone(error_t ok) {
    if (ok == SUCCESS)
      {
	call CollectionControl.start();
	call DisseminationControl.start();
#ifdef DEBUG
	printf("Radio On %lu\n", call LocalTime.get());
        printfflush();
#endif
        if (!CLUSTER_HEAD)
          sendState();
      }
    else
      call RadioControl.start();
  }


  //Empty methods
  event void RadioControl.stopDone(error_t ok) { 
#ifdef DEBUG
    printf("Radio Off %lu\n", call LocalTime.get());
    printfflush();
#endif

#ifdef BLINKY
    call Leds.led1Toggle(); 
#endif
  }



  /** When a message has been successfully transmitted, this event is
      triggered. At this point, we stop the timeout timer, restart the
      sense timer and restart the current-cost if it is needed.
  */
  event void StateSender.sendDone(message_t *msg, error_t ok) {
    if (ok != SUCCESS) {
#ifdef BLINKY
      call Leds.led0Toggle(); 
#endif
      reportError(ERR_SEND_FAILED);    
    }
    else {
      if (last_transmitted_errno < last_errno && last_transmitted_errno != 0.)
	last_errno = last_errno / last_transmitted_errno;
      else
	last_errno = 1.;
    }
  }


  ////////////////////////////////////////////////////////////
  // Produce a nice pattern on start-up
  //
  uint8_t blink_state = 0;

  uint8_t gray[] = { 0, 1, 3, 2, 6, 7, 5, 4 };

  event void BlinkTimer.fired() { 
    if (blink_state >= 60) { /* 30 seconds */
      call Leds.set(0);
    }
    else { 
      blink_state++;
      call BlinkTimer.startOneShot(512L);
      call Leds.set(gray[blink_state % (sizeof gray / sizeof gray[0])]);
    }
  }

  event void SendTimeOutTimer.fired() {
    if (!CLUSTER_HEAD)
      call RadioControl.stop();

    reportError(ERR_NO_ACK);
    my_settings->samplePeriod = DEF_BACKOFF_SENSE_PERIOD;

#ifdef DEBUG
    printf("ack receving failed %lu\n", call LocalTime.get());
    printf("Sample Period to be used %lu\n", my_settings->samplePeriod);
    printfflush();
#endif
    restartSenseTimer();
  }


  //updates SIP models and restarts sense timers and calculate duty time
  void ackReceived(){
    uint32_t stop_time;
    uint32_t send_time;
    int i;

    if (!CLUSTER_HEAD)
      call RadioControl.stop();
    call SendTimeOutTimer.stop();

    stop_time = call LocalTime.get();
    //Calculate the next interval
    if (stop_time < send_start_time) // deal with overflow
      send_time = ((UINT32_MAX - send_start_time) + stop_time + 1);
    else
      send_time = (stop_time - send_start_time);
    last_duty = (float) send_time;

    
#ifdef DEBUG
    printf("Time to send %lu\n", send_time);
    printfflush();
#endif 
    
    my_settings->samplePeriod = DEF_SENSE_PERIOD;

    for (i = 0; i < RS_SIZE; i++) { 
      if (call Configured.get(i)) {
	if (i == RS_TEMPERATURE)
	  call TempTrans.transmissionDone();
	else if (i == RS_HUMIDITY)
	  call HumTrans.transmissionDone();
	else if (i == RS_CO2)
	  call CO2Trans.transmissionDone();
      }
    }

    //reset heartbeat period
    periodsToHeartbeat=HEARTBEAT_PERIOD;
    restartSenseTimer();
  }


  /** AckValue.changed
   *
   * - triggered when ack messgaes are disseminated
   * - checks if this ack message is for the packet
   */


  event void AckValue.changed() { 
    const AckMsg *ackMsg = call AckValue.get();
    CRCStruct crs;
    uint16_t crc;

#ifdef DEBUG
    call Leds.led2Toggle();
    printf("ack packet rec at %lu\n", call LocalTime.get());
    printfflush();
#endif

    crs.node_id = ackMsg->node_id;
    crs.seq = ackMsg->seq;
    crc = (nx_uint16_t)call CRCCalc.crc16(&crs, sizeof crs);

#ifdef DEBUG
    printf("exp seq %u\n", expSeq);
    printf("rec seq %u\n", ackMsg->seq);
    printf("exp nid %u\n", TOS_NODE_ID);
    printf("rec nid %u\n", ackMsg->node_id);
    printf("exp CRC %u\n", crc);
    printf("rec CRC %u\n", ackMsg->crc);
    printfflush();
#endif 
    
    //check crc's, nid and seq match
    if (crc == ackMsg->crc)
      if (TOS_NODE_ID == ackMsg->node_id)
	if (expSeq == ackMsg->seq)
	  ackReceived();	  
    return;
  }
}

