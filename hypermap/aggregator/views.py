from django.http import HttpResponse
from django.template import RequestContext, loader
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.contrib.auth.decorators import login_required

from models import Service, Layer
from tasks import check_service, check_layer
from enums import SERVICE_TYPES


def serialize_checks(check_set):
    """
    Serialize a check_set for raphael
    """
    check_set_list = []
    for check in check_set.all()[:25]:
        check_set_list.append(
            {
                'datetime': check.checked_datetime.isoformat(),
                'value': check.response_time,
                'success': 1 if check.success else 0
            }
        )
    return check_set_list


def index(request):
    # services = Service.objects.annotate(
    #    num_checks=Count('resource_ptr__check')).filter(num_checks__gt=0)
    # services = Service.objects.filter(check__isnull=False)
    order_by = request.GET.get('order_by', '-last_updated')
    filter_by = request.GET.get('filter_by', None)
    # order_by
    if 'total_checks' in order_by:
        services = Service.objects.annotate(total_checks=Count('resource_ptr__check')).order_by(order_by)
    elif 'layers_count' in order_by:
        services = Service.objects.annotate(layers_count=Count('layer')).order_by(order_by)
    else:
        services = Service.objects.all().order_by(order_by)
    # filter_by
    if filter_by:
        services = services.filter(type__exact=filter_by)
    # types filter
    type_dict = {}
    for service_type in SERVICE_TYPES:
        service_type_code = service_type[0]
        service_type_count = Service.objects.filter(type__exact=service_type_code).count()
        type_dict[service_type_code] = service_type_count
    # stats
    layers_count = Layer.objects.all().count()
    services_count = Service.objects.all().count()

    template = loader.get_template('aggregator/index.html')
    context = RequestContext(request, {
        'services': services,
        'type_dict': type_dict,
        'layers_count': layers_count,
        'services_count': services_count,
    })
    return HttpResponse(template.render(context))


def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    resource = serialize_checks(service.check_set)
    if request.method == 'POST':
        check_service.delay(service)
    return render(request, 'aggregator/service_detail.html', {'service': service, 'resource': resource})


def layer_detail(request, layer_id):
    layer = get_object_or_404(Layer, pk=layer_id)
    resource = serialize_checks(layer.check_set)
    if request.method == 'POST':
        check_layer.delay(layer)
    return render(request, 'aggregator/layer_detail.html', {'layer': layer, 'resource': resource})


@login_required
def celery_monitor(request):
    """
    A raw celery monitor to figure out which processes are active and reserved.
    """
    from hypermap import celery_app
    inspect = celery_app.control.inspect()
    active_json = inspect.active()
    reserved_json = inspect.reserved()

    active_tasks = []
    if active_json:
        for worker in active_json.keys():
            for task in active_json[worker]:
                id = task['id']
                # not sure why these 2 fields are not already in AsyncResult
                name = task['name']
                time_start = task['time_start']
                args = task['args']
                active_task = celery_app.AsyncResult(id)
                active_task.name = name
                active_task.args = args
                active_task.worker = worker
                active_task.time_start = time_start
                active_tasks.append(active_task)

    reserved_tasks = []
    if reserved_json:
        for worker in active_json.keys():
            for task in reserved_json[worker]:
                id = task['id']
                name = task['name']
                args = task['args']
                reserved_task = celery_app.AsyncResult(id)
                reserved_task.name = name
                reserved_task.args = args
                reserved_task.worker = worker
                reserved_tasks.append(reserved_task)

    # import ipdb; ipdb.set_trace()

    return render(
        request,
        'aggregator/celery_monitor.html',
        {
            'active_tasks': active_tasks,
            'reserved_tasks': reserved_tasks
        }
    )
