from urllib.parse import urljoin
from flask import Blueprint, render_template, request
from werkzeug.contrib.atom import AtomFeed
from teknologkoren_se.models import User, Post, Event


mod = Blueprint('general', __name__)


@mod.route('/om-oss/')
def om_oss():
    """Show about page."""
    return render_template('general/om-oss.html')


@mod.route('/boka/')
def boka():
    """Show booking page."""
    return render_template('general/boka.html')


@mod.route('/sjung/')
def sjung():
    """Show audition page."""
    return render_template('general/sjung.html')


@mod.route('/kontakt/')
def kontakt():
    """Show contact page.

    Order of board members and their email addresses are hard coded.
    The template iterates over the list of tags and gets the user from
    the generated dict to display them in the same order every time.
    """
    board = {}
    board_tags = [('Ordförande', 'ordf@teknologkoren.se'),
                  ('Vice ordförande', 'vice@teknologkoren.se'),
                  ('Kassör', 'pengar@teknologkoren.se'),
                  ('Sekreterare', 'sekr@teknologkoren.se'),
                  ('PRoletär', 'pr@teknologkoren.se'),
                  ('Notfisqual', 'noter@teknologkoren.se'),
                  ('Qlubbmästare', 'qm@teknologkoren.se')]

    # We cannot iterate over the same list we are remove items from
    tags_copy = list(board_tags)

    # Create a dictionary of the board, eg:
    # {'Ordförande': <user object>, 'Vice ordförande': <user object>}
    for tag_tuple in tags_copy:
        tag, email = tag_tuple

        board_member = User.query.filter(User.has_tag(tag)).first()

        if board_member:
            board[tag] = board_member

        else:
            # There was no user with that tag, remove it from the list
            # the template iterates over.
            board_tags.remove(tag_tuple)

    return render_template(
        'general/kontakt.html',
        board=board,
        tags=board_tags)


@mod.route('/feed/')
def atom_feed():
    """Generate and return rss-feed."""
    feed = AtomFeed("Teknologkören", feed_url=request.url,
                    url=request.url_root)

    posts = (Post.query
             .filter_by(published=True)
             .order_by(Post.timestamp.desc())
             .limit(15))

    for post in posts:
        if isinstance(post, Event):
            path_base = "konserter/"
        else:
            path_base = "blog/"

        feed.add(post.title,
                 post.content_to_html(),
                 content_type='html',
                 author=post.author,
                 url=urljoin(request.url_root, path_base+post.url),
                 updated=post.timestamp
                 )

    return feed.get_response()
