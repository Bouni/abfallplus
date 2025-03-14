# AbfallPlus

----

> [!WARNING]  
> This integration is no longer maintained!
> 
> I highly recommentd to use [Waste Collection Schedule](https://github.com/mampfes/hacs_waste_collection_schedule) in combination with [TrashCard](https://github.com/idaho/hassio-trash-card).

----

[![Validate with hassfest](https://github.com/Bouni/abfallplus/actions/workflows/hassfest.yml/badge.svg)](https://github.com/Bouni/abfallplus/actions/workflows/hassfest.yml)
[![Validate with HACS Action](https://github.com/Bouni/abfallplus/actions/workflows/hacs.yml/badge.svg)](https://github.com/Bouni/abfallplus/actions/workflows/hacs.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

<a href="https://ko-fi.com/I3I364QTM" target="_blank"><img src="https://ko-fi.com/img/githubbutton_sm.svg" height="30px"/></a> <a href="https://www.buymeacoffee.com/bouni" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" height="30px"/></a> <a href="https://github.com/sponsors/Bouni" target="_blank"><img src="https://img.shields.io/badge/-Github Sponsor-fafbfc?style=flat&logo=GitHub%20Sponsors" height="30px"/></a>

This component has been created to be used with Home Assistant.

AbfallPlus allows you to get upcoming municipal waste pick up dates into Home Assistant.

## Data source

The data is fetched from `https://api.abfallplus.de`

### Installation:

#### HACS

- Ensure that HACS is installed.
- Search for and install the "AbfallPlus" integration.
- Restart Home Assistant.

#### Manual installation

- Download the latest release.
- Unpack the release and copy the custom_components/abfallplus directory into the custom_components directory of your Home Assistant installation.
- Restart Home Assistant.

### Example entry for configuration.yaml

```
- platform: abfallplus
  name: Bio Tonne
  key: 5b0384147b5bc055c30fee1fb6db6f76
  municipality: 270
  street: 15720
  trash_ids: "51, 17, 48, 31, 43, 20, 321"
  pattern: Biotonne
```

 - `name` is optional, this defines the friendly name of the sensor
 - `key` is required, the API key of the waste management agency (see details below)
 - `municipality` is required, the ID of the municipality (see details below)
 - `street` is required, the ID of the street (see details below)
 - `trash_ids` is required, the IDs of the trash IDs you want to receive (see details below)
 - `pattern` is optional, filter waste types depending on this keyword 

This gives you a `sensor` in Home-Assiatnt that's called `sensor.bio_tonne` which has the next collection date as it's state:

![image](https://user-images.githubusercontent.com/948965/155665244-52ab32bd-c6a8-45ab-b1fd-cd4ad402bd46.png)

### How to get all the IDs

Here we come to the Problem of this Integration. AbfallPlus does not have a open documented API but we use the API calls that are made by the waste management agency.
I describe by the example of my waste management agency how to get all the IDs and the API key.
The IDs seem to be the database indices and are kind of arbitrary.

#### The waste management agency key

Go the the website of your waste management agency, `https://www.abfall-landkreis-waldshut.de/de/termine/abfuhrtage.php` in my case.
Open the Developer tools of your browser select the networking tab and refresh the page.

You should see at least one call to `api.abfallplus.de`, in my case `https://api.abfallplus.de/index.php?key=5b0384147b5bc055c30fee1fb6db6f76`
As you can see, the key is passed as an GET parameter.

#### The IDs

Usually you have a dropdown on the page that lets you select your municipality. 
If thats done there is another pull down that lets you select your street.

After all selections are made, there is a dropdown that allows you to select between various output formats such as PDF, CSV or ICS.
It doesn't matter which one you select, just click the export button.

You should see a POST request that hast several form values as parameters, here's mine for example:

```
"f_id_kommune":"270",
"f_id_strasse":"15720",
"f_id_abfalltyp_0":"51",
"f_id_abfalltyp_1":"17",
"f_id_abfalltyp_2":"48",
"f_id_abfalltyp_3":"31",
"f_id_abfalltyp_4":"43",
"f_id_abfalltyp_5":"20",
"f_id_abfalltyp_6":"321",
"f_abfallarten_index_max":"7",
"f_abfallarten":"51,17,48,31,43,20,321",
"f_zeitraum":"20200101-20201231",
"f_export_als":"{'action':'https://api.abfallplus.de/?key=5b0384147b5bc055c30fee1fb6db6f76&modus=d6c5855a62cf32a4dadbc2831f0f295f&waction=export_ics','target':''}"
```

 - `f_id_kommune` is your value for municipality
 - `f_id_strasse` is your street
 - `f_abfallarten` is your trash_ids value

❗ In some cases you'll get something like this where `f_id_strasse` is not a number:

```
"f_id_kommune": "2593",
"f_id_bezirk": "492,493",
"f_id_strasse": "2593bauernschaften",
"f_id_strasse_hnr": "496"
```
In that case you can use `f_id_strasse_hnr` for the `street` config value!
