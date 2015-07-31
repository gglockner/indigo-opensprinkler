# indigo-opensprinkler
OpenSprinkler plugin for Indigo

Written by Greg Glockner

## Description
With this plugin, you can control or schedule OpenSprinkler via an
Indigo server. Using weather data in Indigo, you can use weather
conditions to determine how much to water your lawn.

## Installation
0. Download the repository zip file and uncompress it
0. Double-click on the OpenSprinkler Indigo plugin
0. Add a new OpenSprinkler device, and set the Model to OpenSprinkler Module
0. Configure the Network address and the OpenSprinkler password

## Creating a schedule in Indigo
0. Create a new schedule event in Indigo
0. In Actions, select Run Device Actions > Sprinkler Controls > Run Schedule
0. Select your sprinkler device
0. Set the times, in minutes

*Note*: Any schedules you create in Indigo will be in addition to any
schedules you create in OpenSprinkler. You may want to delete any
schedules in OpenSprinkler.

## Known issues
- Requires OpenSprinkler firmware 2.1.3 or newer
- The OpenSprinkler device must have a password set
- You must have some way to identify the OpenSprinkler device on your local network, either via a fixed IP address or a hostname
- If you have multiple sprinkler stations, they must be contiguous; the plugin will not recognize gaps in the list of stations