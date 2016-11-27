from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from wtforms import BooleanField, FormField
from app.views.users import verify_email
from app.forms import EditUserForm, FullEditUserForm, FlaskForm
from app.models import User, Tag, UserTag
from app.util import ts, send_email

mod = Blueprint('intranet', __name__, url_prefix='/intranet')


@mod.before_request
@login_required
def before_request():
    pass


@mod.route('/')
def index():
    return render_template('intranet/intranet.html')


@mod.route('/profile/')
def my_profile():
    return redirect(url_for('.profile', id=current_user.id))


@mod.route('/profile/<int:id>/')
def profile(id):
    user = get_object_or_404(User, User.id == id)
    tags = (Tag
            .select()
            .join(UserTag)
            .where(UserTag.user == user))

    if current_user.id == id or 'Webmaster' in current_user.tags:
        edit = True
    else:
        edit = False

    return render_template(
            'intranet/profile.html',
            user=user,
            tags=tags,
            edit=edit)


@mod.route('/profile/<int:id>/edit/', methods=['GET', 'POST'])
def edit_user(id):
    if 'Webmaster' in current_user.tags:
        return full_edit_user(id)

    elif current_user.id != id:
        return redirect(url_for('.profile', id=id))

    user = current_user
    form = EditUserForm(user, request.form, user)

    if form.validate_on_submit():
        if form.email.data != user.email:
            verify_email(user, form.email.data)
            flash("Please check {} for a verification link."
                  .format(form.email.data))

        user.phone = form.phone.data

        if form.password.data:
            user.password = form.password.data

        user.save()

        return redirect(url_for('.profile', id=id))

    return render_template('intranet/edit_user.html',
                           user=current_user,
                           form=form,
                           full_form=False)


def full_edit_user(id):
    user = get_object_or_404(User, User.id == id)

    class F(FlaskForm):
        pass

    for tag in Tag.select():
        if tag.name in user.tags:
            field = BooleanField(tag.name, default=True)
        else:
            field = BooleanField(tag.name)

        setattr(F, tag.name, field)

    setattr(FullEditUserForm, 'tags', FormField(F))
    form = FullEditUserForm(user, request.form, user)

    if form.validate_on_submit():
        if form.email.data != user.email:
            verify_email(user, form.email.data)
            flash("A verification link has been sent to {}"
                  .format(form.email.data))

        user.phone = form.phone.data

        if form.password.data:
            user.password = form.password.data

        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.active = form.active.data

        tag_form = form.tags
        for tag in Tag.select():
            tag_field = getattr(tag_form, tag.name)

            if tag_field.data and tag.name not in user.tags:
                UserTag.create(user=user, tag=tag)

            elif not tag_field.data and tag.name in user.tags:
                user_tag = UserTag.get(UserTag.user == user and
                                       UserTag.tag == tag)
                user_tag.delete_instance()

        user.save()

        return redirect(url_for('.profile', id=id))

    return render_template('intranet/edit_user.html',
                           user=current_user,
                           form=form,
                           full_form=True)


@mod.route('/members/')
def members():
    users = User.select().where(User.active == True)
    voices = {}
    voice_tags = ['Sopran 1', 'Sopran 2', 'Alt 1', 'Alt 2', 'Tenor 1',
                  'Tenor 2', 'Bas 1', 'Bas 2']
    for voice in voice_tags:
        voices[voice] = (users
                         .join(UserTag)
                         .join(Tag)
                         .where(Tag.name == voice))

    return(render_template(
        'intranet/members.html',
        voices=voices,
        voice_tags=voice_tags))
