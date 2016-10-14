import datetime
from flask import abort, Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from werkzeug.datastructures import CombinedMultiDict
from app import app, images
from app.forms import EditEventForm
from app.models import Event


mod = Blueprint('events', __name__, url_prefix='/konserter')


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['image_url'] = images.url


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def overview(page):
    if current_user.is_authenticated:
        events = Event.select().order_by(Event.start_time)
    else:
        events = Event.select().where(Event.published == True
                                      ).order_by(Event.start_time)

    events = events.order_by(Event.start_time.desc())

    pagination = events.paginate(page, 5)

    if not pagination and events:
        last_page = (len(events) // 5) + 1
        if len(events) % 5:
            last_page += 1
        return redirect(url_for('.konserter', page=last_page))

    has_next = True if events.paginate(page+1, 5) else False

    return render_template('events/overview.html',
                           pagination=pagination,
                           page=page,
                           has_next=has_next)


@mod.route('/new-event/', methods=['GET', 'POST'])
@login_required
def new_event():
    form = EditEventForm(CombinedMultiDict((request.form, request.files)))
    if form.validate_on_submit():
        event = Event.create(
                title=form.title.data,
                content=form.content.data,
                published=form.published.data,
                start_time=form.start_time.data,
                location=form.location.data,
                timestamp=datetime.datetime.now(),
                author=current_user.id,
                image=images.save(form.upload.data)
                )
        return redirect(url_for('.view_event', slug=event.slug))

    return render_template('events/edit-event.html', form=form)


@mod.route('/<slug>/')
def view_event(slug):
    event = get_object_or_404(Event, Event.slug == slug)

    if not event.published and not current_user.is_authenticated:
        return abort(404)

    return render_template('events/view-event.html', event=event)


@mod.route('/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit_event(slug):
    event = get_object_or_404(Event, Event.slug == slug)
    form = EditEventForm(
            CombinedMultiDict((request.form, request.files)),
            event
            )

    if form.validate_on_submit():
        event.title = form.title.data
        event.content = form.content.data
        event.published = form.published.data
        event.start_time = form.start_time.data
        event.location = form.location.data
        event.image = images.save(form.upload.data)
        event.save()
        return redirect(url_for('.view_event', slug=event.slug))

    return render_template('events/edit-event.html', form=form)


@mod.route('/<slug>/remove/')
@login_required
def remove_event(slug):
    event = get_object_or_404(Event, Event.slug == slug)
    event.delete_instance()
    return redirect(url_for('.overview'))
