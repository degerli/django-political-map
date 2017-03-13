from __future__ import unicode_literals

from django.test import TestCase, override_settings
from .models import PoliticalPlace, MapItem
from .utils import country_to_continent
from .backends import Client
from .exceptions import GeoTypeException, NoResultsException
from .widgets import PlaceWidget
#from .forms import PoliticalPlaceForm
from googlemaps.exceptions import HTTPError


class PlaceWidgetTest(TestCase):
    maxDiff = None

    def setUp(self):
        self.placewidget = PlaceWidget()

    def test_place_widget_media(self):
        self.assertHTMLEqual(
            str(self.placewidget.media),
            """<link href="/static/politicalplaces/css/politicalplaces.css" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js"></script>
<script type="text/javascript" src="/static/politicalplaces/js/politicalplaces.js"></script>
<script type="text/javascript" src="https://maps.googleapis.com/maps/api/js?language=en&amp;key=AIzaSyCQbVeTVyl1eUDzJbgpoSTaCb_9wHq1kik"></script>"""
        )

    def test_place_widget_render(self):
        self.assertHTMLEqual(
            str(self.placewidget.render(
                'myfield', 'myvalue', attrs={'id': 'idtest'})),
            """<input id='idtest' name="myfield" type="text" value="myvalue" /><div class='place-search' id="search_map_idtest">search</div>
<div class="place-widget" style="margin-top: 4px">
    <div class='place-panel' id="panel_idtest"></div>
    <div class='place-map-canvas' id="map_canvas_idtest" style="height: 300px; width: 500px;"></div>
</div>

<script>
jQuery(function($) {
  function setVariables(field_id, field_name){
    // not working with multiple PlaceFields.
    // Probably needing an array of variables or something...
    panel = $('#panel_'+field_id);
    map_canvas = document.getElementById('map_canvas_'+field_id);
    search_map = $('#search_map_'+field_id);
    address_input = $('#id_'+field_name);
  }

  setVariables('idtest', 'myfield');
  initMap();
})
</script>
"""
        )


class BackendTest(TestCase):

    def test_init_client(self):
        from .backends import googlemaps
        self.assertTrue(googlemaps.Client)

    @override_settings(LANGUAGE_CODE='en-us')
    def test_geocode(self):
        client = Client()
        res = client.geocode("Roma, IT")
        self.assertEqual(
            "Rome, Italy",
            res[0]['formatted_address'])


class UtilsTest(TestCase):

    def test_country_to_continent(self):
        self.assertEqual(
            "Europe", country_to_continent("Italy"))
        self.assertEqual(
            "Europe", country_to_continent("Czechia"))
        self.assertEqual(
            "Africa", country_to_continent("Senegal"))
        self.assertEqual(
            "South America", country_to_continent("Colombia"))

    def test_country_to_continent_none(self):
        self.assertFalse(country_to_continent("Klingon"))


class PoliticalPlaceModelTest(TestCase):

    def setUp(self):
        self.address = "via Luigi Gastinelli 118, Rome, Italy"
        self.test_place = PoliticalPlace(
            address=self.address)
        self.test_place_wrong_addr = PoliticalPlace(
            address="qwertyuiop")

    def test_unicode_str(self):
        test_place = PoliticalPlace.get_or_create_from_address(
            self.address)
        self.assertEqual(
            str(test_place),
            "Via Luigi Gastinelli, 118, 00132 Roma RM, Italy")

    def test_latlng_property_empty_geocode(self):
        self.assertFalse(self.test_place.lat)
        self.assertFalse(self.test_place.lng)

    def test_political_place_create_map_items(self):
        self.test_place.continent = 'Europe'
        self.test_place.country = 'Italy'
        self.test_place.administrative_area_level_1 = 'Lazio'
        client = Client()
        lat = '41.6552418'
        lng = '12.989615'
        self.test_place._create_map_items(client, lat, lng)
        self.assertEqual(
            "Europe", self.test_place.continent_item.long_name)
        self.assertEqual(
            "Italy", self.test_place.country_item.long_name)
        self.assertEqual(
            "Lazio",
            self.test_place.administrative_area_level_1_item.long_name)
        self.assertFalse(
            self.test_place.administrative_area_level_2_item)
        self.assertFalse(
            self.test_place.administrative_area_level_3_item)
        self.assertFalse(
            self.test_place.locality_item)
        self.assertFalse(
            self.test_place.sublocality_item)

    def test_political_place_create_map_items_no_continent(self):
        self.test_place.country = 'Italy'
        client = Client()
        lat = '41.6552418'
        lng = '12.989615'
        self.test_place._create_map_items(client, lat, lng)
        self.assertEqual(
            "Italy", self.test_place.country_item.long_name)

    def test_political_place_get_or_create_from_address_fields_creation(self):
        test_place = PoliticalPlace.get_or_create_from_address(
            self.address)
        self.assertEqual(
            test_place.administrative_area_level_1,
            "Lazio")
        self.assertEqual(
            test_place.country,
            "Italy")

    def test_political_place_get_or_create_from_address_fields_creation2(self):
        test_place = PoliticalPlace.get_or_create_from_address(
            "Praha")
        self.assertEqual(
            test_place.locality,
            "Prague")
        self.assertEqual(
            test_place.country,
            "Czechia")
        self.assertEqual(
            test_place.continent,
            "Europe")

    def test_political_place_get_or_create_from_address_items_creation(self):
        test_place = PoliticalPlace.get_or_create_from_address(
            self.address)
        self.assertEqual(
            test_place.administrative_area_level_1_item.long_name,
            "Lazio")
        self.assertEqual(
            test_place.country_item.short_name,
            "IT")

    def test_political_place_get_or_create_from_address_url_parent(self):
        test_place = PoliticalPlace.get_or_create_from_address(
            "Montesacro, Rome")
        map_item_italy = MapItem.objects.get(
            long_name__iexact='Italy',
            geo_type__iexact='country')
        map_item_lazio = MapItem.objects.get(
            long_name__iexact='Lazio',
            geo_type__iexact='administrative_area_level_1')
        map_item_rome_area3 = MapItem.objects.get(
            long_name__icontains='Rome',
            geo_type__iexact='administrative_area_level_3')
        map_item_roma = MapItem.objects.get(
            long_name__iexact='Rome',
            geo_type__iexact='locality')
        self.assertEqual(
            test_place.administrative_area_level_1_item.relative_url,
            "/europe/it/lazio/{}".format(map_item_lazio.pk))
        self.assertEqual(
            test_place.administrative_area_level_1_item.parent,
            map_item_italy)
        self.assertEqual(
            test_place.locality_item.relative_url,
            "/europe/it/lazio/rm/rome/rome/{}".format(
                map_item_roma.pk))
        self.assertEqual(
            test_place.locality_item.parent,
            map_item_rome_area3)

    def test_political_place_process_address_wrong(self):
        with self.assertRaises(NoResultsException):
            PoliticalPlace.get_or_create_from_address(
                self.test_place_wrong_addr.address)

    def test_political_place_link_map_items(self):
        self.test_place.geocode = "41.6552418,12.989615"
        self.test_place.place_id = ""
        self.test_place.address = "Lazio, Italy"
        self.test_place.country = "Italy"
        self.test_place.administrative_area_level_1 = "Lazio"
        self.test_place.link_map_items()
        self.assertEqual(
            self.test_place.administrative_area_level_1_item.long_name,
            "Lazio")
        self.assertEqual(
            self.test_place.country_item.short_name,
            "IT")
        self.assertEqual(
            self.test_place.continent_item.long_name,
            "Europe")

    def test_refresh_data(self):
        self.test_place.refresh_data()
        self.assertEqual(
            self.test_place.country_item.short_name, "IT")

    def test_refresh_data_place_id(self):
        self.test_place.place_id = "ChIJu46S-ZZhLxMROG5lkwZ3D7k"
        self.test_place.save()
        self.test_place.refresh_data()
        self.assertEqual(
            self.test_place.country_item.short_name, "IT")


class MapItemModelTest(TestCase):

    def setUp(self):
        self.test_item = MapItem.update_or_create_from_address(
            "Lazio, Italy", 'administrative_area_level_1')

    def test_unicode_str(self):
        self.assertEqual(
            str(self.test_item),
            "Lazio(administrative_area_level_1)")

    def test_get_or_create_from_place_id_create(self):
        place_id = "ChIJNWU6NebuJBMRKYWj8WSQSm8"
        map_item = MapItem.update_or_create_from_place_id(place_id)
        self.assertEqual(map_item.long_name, "Lazio")
        self.assertEqual(map_item.short_name, "Lazio")
        self.assertEqual(map_item.geo_type, "administrative_area_level_1")
        self.assertEqual(
            map_item.types, "administrative_area_level_1,political")
        self.assertEqual(map_item.geocode, "41.6552418,12.989615")
        self.assertEqual(
            map_item.place_id,
            'ChIJNWU6NebuJBMRKYWj8WSQSm8')

    def test_get_or_create_from_place_id_error(self):
        place_id = "qwertyuiop"
        with self.assertRaises(HTTPError):
            MapItem.update_or_create_from_place_id(place_id)

    def test_get_or_create_from_address_create(self):
        address = "Lazio, Italy"
        map_item = MapItem.update_or_create_from_address(
            address, 'administrative_area_level_1')
        self.assertEqual(map_item.long_name, "Lazio")
        self.assertEqual(map_item.short_name, "Lazio")
        self.assertEqual(map_item.geo_type, "administrative_area_level_1")
        self.assertEqual(
            map_item.types, "administrative_area_level_1,political")
        self.assertEqual(map_item.geocode, "41.6552418,12.989615")
        self.assertEqual(
            map_item.place_id,
            'ChIJNWU6NebuJBMRKYWj8WSQSm8')

    def test_get_or_create_from_address_error(self):
        address = "qwertyuiop"
        with self.assertRaises(NoResultsException):
            MapItem.update_or_create_from_address(
                address, 'administrative_area_level_1')

    def test_get_or_create_from_address_wrong_geo_type(self):
        address = "Lazio, Italy"
        with self.assertRaises(GeoTypeException):
            MapItem.update_or_create_from_address(
                address, 'country')

    def test_get_or_create_from_address_get(self):
        self.assertEqual(1, MapItem.objects.count())
        address = "Calabria, Italy"
        MapItem.update_or_create_from_address(
            address, 'administrative_area_level_1')
        self.assertEqual(2, MapItem.objects.count())
        MapItem.update_or_create_from_address(
            address, 'administrative_area_level_1')
        self.assertEqual(2, MapItem.objects.count())

    def test_get_or_create_from_address_africa(self):
        address = "Kayuma"
        map_item = MapItem.update_or_create_from_address(
            address, 'locality')
        self.assertEqual(map_item.long_name, "Kayuma")
        self.assertEqual(map_item.short_name, "Kayuma")
        self.assertEqual(map_item.geocode, "-9.383333,21.833333")
        self.assertEqual(
            map_item.place_id,
            'ChIJ4_CniEcdKxoRb3-I6gCh7II')

    def test_get_or_create_from_address_america(self):
        address = "Dosquebradas, Pereira"
        map_item = MapItem.update_or_create_from_address(
            address, 'locality')
        self.assertEqual(map_item.long_name, "Dosquebradas")
        self.assertEqual(map_item.short_name, "Dosquebradas")
        self.assertEqual(map_item.geocode, "4.8318256,-75.68056779999999")
        self.assertEqual(
            map_item.place_id,
            'ChIJhyRrTd-AOI4ReAs5SWb4f5s')

    def test_get_or_create_from_address_asia(self):
        address = "Tokachi District, Japan"
        map_item = MapItem.update_or_create_from_address(
            address, 'locality')
        self.assertEqual(map_item.long_name, "Tokachi District")
        self.assertEqual(map_item.short_name, "Tokachi District")
        self.assertEqual(map_item.geocode, "42.913886,143.6932779")
        self.assertEqual(
            map_item.place_id,
            'ChIJF1BfXpK2c18R4BivzcAmO9M')

    def test_get_or_create_from_address_europe(self):
        address = "Hordaland, Norway"
        map_item = MapItem.update_or_create_from_address(
            address, 'administrative_area_level_1')
        self.assertEqual(map_item.long_name, "Hordaland")
        self.assertEqual(map_item.short_name, "Hordaland")
        self.assertEqual(map_item.geocode, "60.2733674,5.7220194")
        self.assertEqual(
            map_item.place_id,
            'ChIJU9YJbagwPEYR0ByzKCZ3AQM')

    def test_get_or_create_from_address_oceania(self):
        address = "Tonga"
        map_item = MapItem.update_or_create_from_address(
            address, 'country')
        self.assertEqual(map_item.long_name, "Tonga")
        self.assertEqual(map_item.short_name, "TO")
        self.assertEqual(map_item.geocode, "-21.178986,-175.198242")
        self.assertEqual(
            map_item.place_id,
            'ChIJHdCfu0S2k3ERqeJexcrMbfM')
