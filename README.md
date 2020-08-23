A quick and dirty integration for Home Assistant to integrate PurpleAir
air quality sensors. This will create an `air_quality` sensor with the
relevant data and create an additional AQI `sensor` for ease-of-use.

Simply copy the `/purpleair` directory in to your config's
`custom_components` directory (you may need to create it), restart Home
Assistant, and add the integration via the UI (it's simple!).

To find a sensor to integrate:

1. Look at the [PurpleAir Map][1].
2. Find and click an available _outdoor_ station (indoor won't do you
   any good).
3. In the station pop up, click on "Get This Widget".
4. Right-click the "JSON" link at the bottom of the black box and copy
   the link. (Copy Link Location, et al.)
5. Go to Home Assistant and go to the Integrations Page.
6. Add the PurpleAir integration.
7. Paste the link and finish.

You'll have two entities added: an `air_quality` entity and a `sensor`
entity. The air quality fills out all available values via the state
dictionary, and the sensor entity is simply the calculated AQI value,
for ease of use. (The AQI also shows up as an attribute on the air
quality entity as well).

Sensor data on PurpleAir is only updated every two minutes, and to be
nice, this integration will batch its updates every five minutes. If you
add multiple sensors, the new sensors will take up to five minutes to
get their data, as to not flood their free service with requests.

This component is licensed under the MIT license, so feel free to copy,
enhance, and redistribute as you see fit.

### Notes
This was a very single-day project, so it works for outdoor sensors that
report an A and B channel. It _should_ work with a single channel sensor
as well, but I didn't test that.

This uses the free API to access the data. If you have your own sensors
being published and have them marked as private, you'll need to modify
this source to allow you to authenticate to view your data with your
Google account (I think, it was mentioned in their FAQ).

I don't have any local devices, so this will not currently work with
sensors on your internal network. It should be simple to add it, but I
have no way to test it. It sounds like the payload is slightly different
and the URL is private. This code simply extracts the given sensor ID to
batch the `/json` requests (the site is hard-coded too, I just use the
full URL to start).

[1]: http://www.purpleair.com/map?mylocation
