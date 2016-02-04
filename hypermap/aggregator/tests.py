from django.test import TestCase
from django.core.urlresolvers import reverse
import re
import json
from models import Service, Layer, Check
from arcrest import MapService as ArcMapService, ImageService as ArcImageService

SERVICE_NUMBER = 10
LAYER_PER_SERVICE_NUMBER = 20
TIMES_TO_CHECK = 3


class AggregatorTestCase(TestCase):

    def setUp(self):

        for s in range(0, SERVICE_NUMBER):
            service = Service(
                url='http://%s.fakeurl.com' % s,
                title='Title %s' % s,
                type='OGC:WMS',
            )
            service.save()
            for l in range(0, 20):
                layer = Layer(
                    name='Layer %s, from service %s' % (l, s),
                    bbox_x0=-179,
                    bbox_x1=179,
                    bbox_y0=-89,
                    bbox_y1=89,
                    service=service
                )
                layer.save()
                service.layer_set.add(layer)
        for c in range(0, TIMES_TO_CHECK):
            for s in range(0, SERVICE_NUMBER):
                service = Service.objects.all()[s]
                service.check()
                for layer in service.layer_set.all():
                    layer.check()

    def test_checks_count(self):
        total_checks = (
            (SERVICE_NUMBER + (SERVICE_NUMBER * LAYER_PER_SERVICE_NUMBER)) * TIMES_TO_CHECK
        )
        self.assertEqual(total_checks, Check.objects.all().count())

    def test_check_status(self):
        check = Check.objects.all()[0]
        self.assertFalse(check.success)

    def test_pages_render(self):
        """
        Verify pages that do and do not require login and corresponding status
        codes
        """

        # anonymous can go to home page
        response = self.client.get(reverse('index'))
        self.assertEqual(200, response.status_code)

        # anonymous going to service_detail is authorized
        service = Service.objects.all()[0]
        response = self.client.get(
            reverse('service_detail', args=(str(service.id),)))
        self.assertEqual(200, response.status_code)

        # anonymous going to layer_detail is authorized
        layer = Layer.objects.all()[0]
        response = self.client.get(
            reverse('layer_detail', args=(str(layer.id),)))
        self.assertEqual(200, response.status_code)

    def test_update_layers_esri(self):
        arcservice = ArcMapService("http://sampleserver1.arcgisonline.com/ArcGIS/rest/services"
                                   "/WaterTemplate/WaterDistributionNetwork/MapServer/?f=json")
        service = Service(title="Test",
                          url="http://sampleserver1.arcgisonline.com/ArcGIS/rest/services"
                              "/WaterTemplate/WaterDistributionNetwork/MapServer/?f=json",
                          type='ESRI')
        service.save()
        # we check if the service exists
        self.assertTrue(re.search("\/MapServer\/*(f=json)*", service.url))
        for esri_layer in arcservice.layers:
            layer = Layer(
                    name=esri_layer.name,
                    bbox_x0=esri_layer.extent.xmin,
                    bbox_x1=esri_layer.extent.ymin,
                    bbox_y0=esri_layer.extent.xmax,
                    bbox_y1=esri_layer.extent.ymax,
                    service=service
                )
            layer.save()
            service.layer_set.add(layer)
        imageservice = ArcImageService("http://sampleserver6.arcgisonline.com/arcgis/rest/services/"
                                       "Toronto/ImageServer/?json")
        service = Service(title="Test",
                          url="http://sampleserver6.arcgisonline.com/ArcGIS/rest/services"
                              "/Toronto/ImageServer/?f=json",
                          type='ESRI')
        service.save()
        # we check if the service exists
        self.assertTrue(re.search("\/ImageServer\/*(f=json)*", service.url))
        obj = json.loads(imageservice._contents)
        layer = Layer(name=obj['name'],
                      bbox_x0=str(obj['extent']['xmin']),
                      bbox_x1=str(obj['extent']['ymin']),
                      bbox_y0=str(obj['extent']['xmax']),
                      bbox_y1=str(obj['extent']['ymax']),
                      service=service)
        layer.save()
        service.layer_set.add(layer)
