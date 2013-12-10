// Generated by CoffeeScript 1.3.3
var setExtremes;

$(document).ready(function() {
  var options, url;
  console.log("Script Called");
  options = {
    chart: {
      renderTo: "theGraph",
      zoomType: "x"
    },
    title: {
      text: "Test RRD"
    },
    rangeSelector: {
      buttons: [
        {
          type: "day",
          count: 1,
          text: "1d"
        }, {
          type: "day",
          count: 3,
          text: "3d"
        }, {
          type: "week",
          count: 1,
          text: "1w"
        }, {
          type: "week",
          count: 2,
          text: "2w"
        }, {
          type: "month",
          count: 1,
          text: "1m"
        }, {
          type: "all",
          text: "all"
        }
      ]
    },
    xAxis: {
      events: {
        afterSetExtremes: setExtremes
      }
    },
    series: []
  };
  console.log(options.series);
  url = "/rrd/";
  $.getJSON(url, {
    hires: false
  }, function(data) {
    var startTime, step, theChart, theSeries;
    console.log("Fetching Data", data);
    startTime = data.meta.start * 1000;
    step = data.meta.step * 1000;
    console.log("Start: ", startTime, "  Step: ", step);
    data = data.data;
    console.log(data);
    theSeries = [
      {
        name: "A Series",
        data: data,
        pointStart: startTime,
        pointInterval: step
      }
    ];
    options.series = theSeries;
    console.log("Options ", options);
    theChart = new Highcharts.StockChart(options);
  });
});

setExtremes = function(e) {
  var currentExt, theChart, url;
  currentExt = this.getExtremes();
  console.log("Extremes ", currentExt);
  console.log("e ", e);
  theChart = $("#theGraph").highcharts();
  theChart.showLoading('Loading Data');
  url = "/rrd/";
  $.getJSON(url, {
    hires: false,
    start: e.min,
    end: e.max
  }, function(data) {
    var startTime, step, theSeries;
    startTime = data.meta.start * 1000;
    step = data.meta.step * 1000;
    theSeries = [
      {
        name: "A Series",
        data: data,
        pointStart: startTime,
        pointInterval: step
      }
    ];
    theChart.series[0] = theSeries;
    theChart.hideLoading();
  });
};