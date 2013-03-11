/* Packets.h - Header file containing all packet formats sent/received

   Copyright (C) 2011 Ross Wilkins

   This File is part of Cogent-House

   Cogent-House is free software: you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation, either version 3 of the
   License, or (at your option) any later version.

   Cogent-House is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program. If not, see
   <http://www.gnu.org/licenses/>.



===================
Packet Header
===================

Header file containing all packet formats sent/received


:author: Ross Wilkins
:email: ross.wilkins87@googlemail.com
:date:  06/01/2011
*/

#ifndef _PACKETS_H
#define _PACKETS_H


// state codes
enum {
  SC_TEMPERATURE = 0,
  SC_D_TEMPERATURE = 1,
  SC_HUMIDITY = 2,
  SC_D_HUMIDITY = 3,
  SC_PAR = 4,
  SC_TSR = 5,
  SC_VOLTAGE = 6,
  SC_D_VOLTAGE = 7,
  SC_CO2 = 8,
  SC_AQ = 9,
  SC_VOC = 10,
  SC_POWER = 11,
  SC_HEAT = 12,
  SC_DUTY_TIME= 13,
  SC_ERRNO = 14,
  SC_POWER_MIN = 15,
  SC_POWER_MAX = 16,
  SC_POWER_KWH = 17,
  SC_HEAT_ENERGY = 18,
  SC_HEAT_VOLUME = 19,
  SC_D_CO2 = 20,
  SC_D_VOC = 21,
  SC_D_AQ = 22,
  SC_BN_TEMP_COUNT = 5,
  SC_BN_TEMP_FIRST = 23,
  SC_BN_HUM_COUNT = 4,
  SC_BN_HUM_FIRST = 28,
  SC_BN_CO2_COUNT = 4,
  SC_BN_CO2_FIRST = 32,
  SC_BN_VOC_COUNT = 2,
  SC_BN_VOC_FIRST = 36,
  SC_BN_AQ_COUNT = 2,
  SC_BN_AQ_FIRST = 38,
  SC_OPTI = 40,
  SC_SIZE = 41, // SC_SIZE must be 1 greater than last entry
};

#include "Node/PackState/packstate.h"

// raw sensors
enum { 
  RS_TEMPERATURE = 0,
  RS_HUMIDITY = 1,
  RS_PAR = 2,
  RS_TSR = 3,
  RS_VOLTAGE = 4,
  RS_CO2 = 5,
  RS_AQ = 6,
  RS_VOC = 7,
  RS_POWER = 8,
  RS_HEATMETER = 9,
  RS_DUTY = 10,
  RS_OPTI = 11,
  RS_CLAMP = 12,
  RS_SIZE = 13 // must be 1 greater than last entry
};


//separate packets structure for mote type

enum {
  AM_ACKMSG = 3,
  AM_STATEV1MSG = 4,
  AM_CONFIGMSG = 5,
  DIS_SETTINGS = 6,
  AM_STATEMSG = 7,
  SPECIAL = 0xc7,
  MAX_HOPS = 4,
  CLUSTER_HEAD_TYPE = 10
};


/* error codes should be prime. As each error occurs during a sense
   cycle, it is multiplied into last_errno. Factorising the
   resulting value gives both the number of occurences and the type.
*/

enum {
  ERR_SEND_CANCEL_FAIL = 2,
  ERR_SEND_TIMEOUT = 3,
  ERR_SEND_FAILED = 5,
  ERR_SEND_WHILE_PACKET_PENDING = 7,
  ERR_SEND_WHILE_SENDING = 11,
  ERR_NO_ACK=13,
  ERR_HEARTBEAT=17
};


enum {
  NODE_TYPE_MAX = 10
};


typedef nx_struct StateMsg {
  nx_uint16_t ctp_parent_id;
  nx_uint32_t timestamp;
  nx_uint8_t special;
  nx_uint8_t seq;
  nx_int16_t rssi;
  nx_uint8_t packed_state_mask[bitset_size(SC_SIZE)];
  nx_float packed_state[SC_SIZE];
} StateMsg; // varies depending on SC_SIZE 


typedef nx_struct ConfigPerType {
  nx_uint32_t samplePeriod;
  nx_bool blink;
  nx_uint8_t configured [bitset_size(RS_SIZE)];
} ConfigPerType;

typedef nx_struct ConfigMsg {
  nx_uint8_t typeCount;
  ConfigPerType byType [NODE_TYPE_MAX];
  nx_uint8_t special;
} ConfigMsg;


typedef struct CRCStruct {
  nx_uint16_t node_id;
  nx_uint16_t seq;
} CRCStruct;


typedef nx_struct AckMsg {
  nx_uint16_t node_id;
  nx_uint8_t seq;
  nx_uint16_t crc;
} AckMsg;


#endif
