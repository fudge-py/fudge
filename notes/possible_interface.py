
# this might make it easier to deal with start/stop/clear_expectations


import fudge

mgr = fudge.manage("soap services")
Weather = mgr.Fake("Weather", patches=["weather_service.Weather"])
Weather = Weather.expects("__init__").expects("get_weather").returns({'temp':'89F'})

with mgr.use_fakes():
    from weather_service import Weather
    w = Weather()
    print w.get_weather()

@mgr.with_fakes
def test_weather():
    from weather_service import Weather
    w = Weather()
    print w.get_weather()

import unittest

class TestWeather(unittest.TestCase):
    
    def setUp(self):
        mgr.start()
    
    def test_weather(self):
        from weather_service import Weather
        w = Weather()
        print w.get_weather()
        mgr.stop()
    