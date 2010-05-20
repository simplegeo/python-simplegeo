## Introduction

The SimpleGeo engineering team uses the [Python client](http://github.com/simplegeo/python-simplegeo) internally, so we thought it would make sense to write a good tutorial on how to use it.

This tutorial is written using Terminal on Mac OS X, but if you are using a PC, you can download an SSH client like [Putty](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html).


## Installation and Requirements

Our Python client requires both `httplib2` and `oauth2`. 

1. Install the requirements:
    * Make sure you have [git](http://code.google.com/p/git-osx-installer/) installed.
    * Download [httplib2](http://code.google.com/p/httplib2/downloads/list) and [oauth2](http://github.com/simplegeo/python-oauth2/downloads) and unpack them. To install, issue the following command: `sudo python setup.py install` in each respective directory.
1. Check out the [GitHub repository](http://github.com/simplegeo/python-simplegeo) and install the `simplegeo` Python module:
    * `git clone http://github.com/simplegeo/python-simplegeo.git`
    * `cd python-simplegeo`
    * `sudo python setup.py install`
1. Test to see if the installation worked:
    * `python`
    * `>>> import simplegeo`
    * `>>> simplegeo`
    * `<module 'simplegeo' from 'simplegeo/__init__.pyc'>`

If you get the above output, everything worked.

_Note: As our client matures, make sure to type `git pull` while in the `python-simplegeo` directory to always get the latest version of the code._


## Creating an Instance of the Client

Fire up Python by typing `python` in your terminal window.

    >>> import simplegeo
    >>> client = simplegeo.Client('your_key', 'your_secret')

You can find your OAuth Token (key) and Secret on the [Account settings page](http://simplegeo.com/account/settings/). 

Once you've set that up, make sure your client was initiated by simply typing `client`:

    >>> client
    http://api.simplegeo.com:80 (your_key, your_secret)

Now you can start making API calls with `client`.


## Getting nearby points using a latitude and longitude with a limit and a radius

Let's do a nearby query using the global public Twitter layer in the center of San Francisco, using a `radius` of 0.5 kilometers. The `get_nearby()` function takes a lat, and a lon. We will `limit` the query to 1 result for brevity:

    >>> client.get_nearby('com.simplegeo.global.twitter', 37.765850, \
                          -122.437094, limit=1, radius=0.5)

You should get a JSON representation of your data:

    {'features': [ {
        'created': 1267864834,
        'distance': 227.29306733689,
        'geometry': { 
            'coordinates': [-122.434517, 37.765988999999998],
            'type': 'Point'
         },
        'id': '10066246075',
        'layerLink': { 
            'href': 'http://api.simplegeo.com/0.1/layer/com.simplegeo. \
                    global.twitter.json'
         }
        'properties': {
            'body': 'I blame San Francisco. #alcohol',
            'expires': 0,
            'layer': 'com.simplegeo.global.twitter',
            'name': 'Jeremy Brown',
            'thumbnail': 'http://img.tweetimag.es/i/brownjava_n.png',
            'type': 'note',
            'url': 'http://twitter.com/brownjava/status/10066246075',
            'userid': 17548554,
            'username': 'brownjava'
        },
        'selfLink': {'href': 'http://api.simplegeo.com/0.1/records/com.simplegeo. \
                             global.twitter/10066246075.json'},
        'type': 'Feature'
        } ],
    'type': 'FeatureCollection'
    }

Please keep in mind that `get_nearby()` function is based on TIGER data and can be a little off depending on the exact placement of the latitude and longitude depending on their relation to the address. It's very, very accurate down to the street block, city, state, and zip code though.


## Getting nearby points using a geohash

You can also do a nearby query using a [geohash](http://geohash.org/):

    >>> client.get_nearby_geohash('com.simplegeo.global.twitter', '9q8y')


## Using the Reverse Geocoder

You can use the `nearby/address/` endpoint to reverse geocode a lat/lon. Here is an example using a lat/lon from the center of San Francisco:

    >>> import simplegeo
    >>> client = simplegeo.Client('your_key', 'your_secret')
    >>> address = client.get_nearby_address(37.76580, -122.43704)
    >>> address

You should see a [GeoJSON](http://geojson.org/) object returned:

    {
       'geometry':{
          'type':'Point',
          'coordinates':[
             -122.437094,
             37.76585
          ]
       },
       'type':'Feature',
       'properties':{
          'state_name':'California',
          'street_number':'2403',
          'country':'US',
          'street':'15th St',
          'postal_code':'94114',
          'county_name':'San Francisco',
          'county_code':'075',
          'state_code':'CA',
          'place_name':'San Francisco'
       }
    }


## Creating a Record

To add a record using the Python client, you must first create a `Record` object:

    >>> from simplegeo import Record
    >>> r = Record('com.simplegeo.test', '4', 37.786521, -122.397850)

Now add the record:

    >>> client.add_record(r)

The bare minimum that you need to add a record is: layer name, unique ID, lat, and lon. Optional parameters are:

 * `type` - a string that defaults to `object`, but can be `person`, `place`, or `media`. If a record's type is `media` you must also set the media property to `text`, `audio`, `video`, or `image`.
 * `created date` - an [epoch](http://en.wikipedia.org/wiki/Unix_time) timestamp. Defaults to current `time()`.
 * `properties` - you can attach any metadata to a Record using [Python keyword arguments](http://docs.python.org/tutorial/controlflow.html#keyword-arguments).

Here is how you would add a more detailed record:

    >>> r = Record('com.simplegeo.test', '4', 37.786521, -122.397850, 'place', \
                   1262304000, foo = 'bar')

A successful API response from adding a record would be a `202`, which means we've received it for processing and it will be available throughout the API shortly. In our experience it generally never takes more than a second for the record to be available across all three data centers.

## Deleting a Record

If you want to delete a record, simply call the `delete_record()` function, which activates the HTTP DELETE method endpoint. It takes two arguments: the layer name and a unique ID.

    >>> client.delete_record('com.simplegeo.test', '4')


## Inserting Records in Batch

Using GeoJSON's `FeatureCollection` format you can input up to 100 records at a time into the API. This is a great way to batch load larger data sets. It should be noted that all writes to SimpleGeo go through a queue so you might see a greater lag when inserting a large number of records using this method. As an example, we've found we can comfortably load 20,000 records every few minutes with a few minute breather.

To add multiple records, pass the layer name and a Python [list](http://docs.python.org/tutorial/datastructures.html#more-on-lists) of `Record`s:

    >>> r1 = Record('com.simplegeo.test', '7', 37.786521, -122.397850, \
                    'place', 1262304000, name = 'Chatz Coffee')
    >>> r2 = Record('com.simplegeo.test', '8', 37.786274, -122.397513, \
                    'place', 1262304000, name = 'CBS Interactive')
    >>> client.add_records('com.simplegeo.test', [r1,r2])


## Fetching a Record by ID

To fetch a single record you can use the `get_record()` or `get_records()` methods. Both take a layer name as the first argument and either a single record ID or an `array` of record IDs for the second argument. If we wanted to fetch the `joestump` record from above, we'd use the following code. The API will respond with a `404` if the record is not found in the system.

    >>> client.get_record('com.simplegeo.global.twitter', 9073364877)

Grab multiple records at a time by passing in an array of unique IDs in string format.

    >>> client.get_records('com.simplegeo.global.twitter', \
                           ['9073757897', '9073313347', '9073364877'])

The first call fetches a single record by its ID and the second fetches an array of records by IDs. If you are needing to fetch multiple records it makes much more sense to fetch using the `get_records()` method to reduce HTTP overhead and reduce the number of calls you make to the API.


## Fetching a Record's History

One of the more interesting features of SimpleGeo's API is that we keep track of where a record has been over time. Every time a record is updated we take the record's previous postion, along with the time it was at that point, and push it into its history. This allows you to ping the API and see where a point has been throughout its history in the system. 

This feature is useful for creating GPS tracks, breadcrumbs, and other historical traces you need to make for records over time and space.

    >>> client.get_history('com.simplegeo.test', 'andrew')

In return, you will receive a GeometryCollection in JSON format:

    {'geometries': [ {
        'coordinates': [-122.39785000000001, 37.786521],
        'created': 1262304100,
        'type': 'Point'}, {
        'coordinates': [-122.39785000000001, 37.786521],
        'created': 1262304000,
        'type': 'Point'}, {
        'coordinates': [-122.392, 37.786513999999997],
        'created': 1262303000,
        'type': 'Point'}],
    'type': 'GeometryCollection'}

If my application had been updating `andrew`'s location over time, then I'd be able to get a history of where `andrew` has been over time. It could also be used to track, say, which post office a particular Netflix DVD has been for a given time period.


## Find all polygons that a given point contains

The `get_contains()` function takes a latitude and longitude, and returns all of the polygons or boundaries containing that point. 

Let's find all of the polygons associated with this point, near Downingtown, PA:

    >>> client.get_contains(40.0064958, -75.7032742)

In the returned response, you will see `Country`, `Province`, `County`, `Urban Area`, `Neighborhood`, `Postal Code`, `Census Tract` and a few others, depending on the geography of your query. Check out our [endpoints page](http://help.simplegeo.com/faqs/api-documentation/endpoints) for more info.


## Find all overlapping polygons and boundaries for a given bounding box

You can use the `get_overlaps()` function to see which polygons overlap a bounding box. The function takes four parameters: `south`, `west`, `north`, `east`. *These are single units of latitude and longitude. Let's explore and example. I'm using the metropolitan area of Grosse Pointe, Michigan:

    >>> south = 42.4166  # Grosse Pointe Farms
    >>> west = -82.9189  # Harper Woods
    >>> north = 42.4465  # Grosse Pointe Woods
    >>> east = -82.8753  # Grosse Pointe Shores

Notice how each value is a single latitude or longitude. Instead of referencing a point, they are referencing a line on the map. Four of these creates a bounding box:

![A bounding box "overlaps" query](http://s3.amazonaws.com/entp-tender-production/assets/7554bf80485472bae96d38d3b2b0140709157b5a/Get_Lat_Lon_-_find_the_latitude_and_longitude_of_a_point_on_a_map_normal.jpg)

_A great tool for finding latitudes and longitudes on a map is called [http://getlatlon.com](http://getlatlon.com/)._

Now let's call the `get_overlaps()` function in the Python interpreter:

    >>> client.get_overlaps(south, west, north, east)

In the returned response, you will see roughly 26 polygons, including three city boundaries, three zip codes, and a few Census tracts. For more information on the `overlaps/` endpoint, check out the [endpoints page](http://help.simplegeo.com/faqs/api-documentation/endpoints).


## Find the boundary of a polygon

If you tried the previous example, you will have noticed the id value `'id': 'County:Wayne:dpsb93'`. You can use the `get_boundary()` function to find the lat/lon boundaries of a given polygon. Here's how it works:

    >>> client.get_boundary('County:Wayne:dpsb93')

In the return response, you will see a valid GeoJSON feature object with all of the lat/lons of that polygon. In this case, 2,616 values were returned in the `geometry` block. More info on this function on the [endpoints page](http://help.simplegeo.com/faqs/api-documentation/endpoints).


## Fetching SpotRank Population Density

We've partnered with Skyhook Wireless to provide access to their amazing SpotRank data. This data provides crowd-sourced population data for about 15% of the globe – mostly in metropolitan areas. 

One thing to note is that this endpoint returns [GeoJSON](http://geojson.org) `Polygon`'s and not `Point`'s like much of the rest of the API. Additionally, GeoJSON `Polygon`'s can be a bit confusing as 5 coordinates are returned rather than a bounding box or just the four points. This is because GeoJSON specifies that you must draw a "ring" around the polygon starting with the most outer ring. You'll see that SpotRank returns tiles that are roughly 100 meters square and that the last point is identical to the first point, which closes the ring.

Let's do a density query for 9am in San Francisco's Financial District:

    >>> client.get_density(37.78652, -122.39785, 'mon', 15)

The third (`day`) and fourth (`hour`) arguments are both optional. If you do not specify a day it will use the current day according to Python's `date()` function, so make sure your timezones and such are set up accordingly. Another thing to note is that you *must* specify an hour if you want a specific hours and that hours are in local time. Below is an example of what the output would look like.

    {'geometry': {
        'coordinates': [ [37.7861328125, -122.3984375],
                         [37.787109375, -122.3984375],
                         [37.787109375, -122.3974609375],
                         [37.7861328125, -122.3974609375],
                         [37.7861328125, -122.3984375]
                       ],
        'type': 'Polygon'
        },
     'properties': {
         'city_rank': 10,
         'dayname': 'mon',
         'hour': 15,
         'local_rank': 9,
         'trending_rank': 0,
         'worldwide_rank': 10
      },
      'type': 'Feature'
      }

To explore the API deeper, check out our [endpoints page](http://help.simplegeo.com/faqs/api-documentation/endpoints).
