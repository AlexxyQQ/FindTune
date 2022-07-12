import os
import secrets
from flask import Blueprint, redirect, request, render_template, url_for
from Backend.utils import From_File
from flask_login import current_user, login_required
from form import UpdateAccountForm, LyricsForm
from __init__ import db, bcrypt, app
from PIL import Image
from models import Songs, user as DBUser, Lyrics
import urllib3
import ast

# from Backend import From_File

views = Blueprint("views", __name__)
t = urllib3.PoolManager()


@views.route("/", methods=["GET", "POST"])
def home():
    return render_template("Home.html")


@app.route("/offline.html")
def offline():
    return render_template("404/pagenotfound.html", title="Pagenotfound")


@app.route("/service-worker.js")
def sw():
    return app.send_static_file("service-worker.js")


@views.route("/search", methods=["GET", "POST"])
def searchsong():
    if request.method == "POST":
        return redirect(url_for("views.song", songname=request.form["Song"]))


@views.route("/check", methods=["GET", "POST"])
def check():
    songname = "notfound"
    if request.method == "POST":
        request.files["file"].save("./audio.wav")
        b = From_File.main("./audio.wav")
        get_youtube_uri = t.request(
            "GET",
            b.get("track").get("sections")[2].get("youtubeurl"),
        )
        dict_str = get_youtube_uri.data.decode("UTF-8")
        youtubeDetail = ast.literal_eval(dict_str)
        try:
            details = Songs(
                title=b.get("track").get("title"),
                artist=b.get("track").get("subtitle"),
                album=b.get("track").get("sections")[0].get("metadata")[0].get("text"),
                year=b.get("track").get("sections")[0].get("metadata")[2].get("text"),
                tagid=b.get("track").get("key"),
                cover_image=b.get("track").get("images").get("coverart"),
                yt_thumbnail=youtubeDetail.get("image").get("url"),
                yt_link=youtubeDetail.get("actions")[0].get("uri"),
            )

            db.session.add(details)
            db.session.commit()
            Song_details = Songs.query.filter_by(
                title=b.get("track").get("title"), artist=b.get("track").get("subtitle")
            ).first()
            # if Song_details != None:
            #     print(Song_details.id)
            #     lyrics = Lyrics(
            #         lyrics=f"""{b.get("track").get("sections")[1].get("text")}""",
            #         song_id=Song_details.id,
            #         user_id=current_user.id,
            #     )
            #     db.session.add(lyrics)
            #     db.session.commit()
        except:
            pass
        return f'{b.get("track").get("title")}-{b.get("track").get("subtitle")}'

    return songname


@views.route("<string:songname>", methods=["GET", "POST"])
def song(songname):
    lyrics_form = LyricsForm()
    if songname != "service-worker.js" and songname != "favicon.ico":
        Song_details = Songs.query.filter_by(
            title=songname.split("-")[0], artist=songname.split("-")[1]
        ).first()
        if Song_details != None:
            song_lyrics = Lyrics.query.filter_by(song_id=Song_details.id).first()
            if current_user.is_authenticated:
                if song_lyrics != None:
                    aa = song_lyrics.lyrics.replace("[", "").replace("]", "")
                    print(aa)
                    l = [
                        '"{}"'.format(aa)
                        for aa in aa.split('"')
                        if aa not in ("", ", ")
                    ]
                    return render_template(
                        "FoundSong/FoundSong.html",
                        song_id=Song_details.id,
                        songname=Song_details.title,
                        artist=Song_details.artist,
                        album=Song_details.album,
                        year=Song_details.year,
                        cover_image=Song_details.cover_image,
                        lyrics=l,
                        uplyric=aa,
                        yt_thumbnail=Song_details.yt_thumbnail,
                        yt_link=Song_details.yt_link,
                        lyrics_form=lyrics_form,
                    )
                else:
                    return render_template(
                        "FoundSong/FoundSong.html",
                        song_id=Song_details.id,
                        songname=Song_details.title,
                        artist=Song_details.artist,
                        album=Song_details.album,
                        year=Song_details.year,
                        cover_image=Song_details.cover_image,
                        lyrics=None,
                        yt_thumbnail=Song_details.yt_thumbnail,
                        yt_link=Song_details.yt_link,
                        lyrics_form=lyrics_form,
                    )

            if song_lyrics != None:
                aa = song_lyrics.lyrics.replace("[", "").replace("]", "")
                l = ['"{}"'.format(aa) for aa in aa.split('"') if aa not in ("", ", ")]
                return render_template(
                    "FoundSong/FoundSong.html",
                    songname=Song_details.title,
                    artist=Song_details.artist,
                    album=Song_details.album,
                    year=Song_details.year,
                    cover_image=Song_details.cover_image,
                    lyrics=l,
                    yt_thumbnail=Song_details.yt_thumbnail,
                    yt_link=Song_details.yt_link,
                )
            else:
                return render_template(
                    "FoundSong/FoundSong.html",
                    songname=Song_details.title,
                    artist=Song_details.artist,
                    album=Song_details.album,
                    year=Song_details.year,
                    cover_image=Song_details.cover_image,
                    lyrics=None,
                    yt_thumbnail=Song_details.yt_thumbnail,
                    yt_link=Song_details.yt_link,
                )
    return render_template("404/pagenotfound.html", title="Pagenotfound")


@views.route("/lyrics_display", methods=["GET", "POST"])
@login_required
def lyrics_display():
    lyrics_form = LyricsForm()
    if request.method == "POST":
        if len(lyrics_form.lyrics.data) > 100:
            if lyrics_form.validate_on_submit():
                lyrics = Lyrics(
                    lyrics=lyrics_form.lyrics.data,
                    song_id=lyrics_form.song_id.data,
                    user_id=current_user.id,
                )
                db.session.add(lyrics)
                db.session.commit()

            else:
                redirect(url_for("views.home"))
    return render_template("404/pagenotfound.html", title="Pagenotfound")


def save_pic(pic):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(pic.filename)
    pic_fn = random_hex + f_ext
    pic_path = os.path.join(app.root_path, "static/Assets/userimage", pic_fn)
    pic.save(pic_path)
    output_size = (250, 250)
    i = Image.open(pic)
    i.thumbnail(output_size)
    i.save(pic_path)
    return pic_fn


@views.route("/@<string:username>", methods=["GET", "POST"])
@login_required
def account(username):
    form = UpdateAccountForm()
    if request.method == "POST":
        if form.validate_on_submit():
            if form.picture.data:
                picture_file = save_pic(form.picture.data)
                current_user.image_file = picture_file
            current_user.username = form.username.data
            db.session.commit()
            return redirect(url_for("views.home"))
        elif request.method == "GET":
            form.username.data = current_user.username

    if DBUser.query.filter_by(username=username).first():
        return render_template(
            "UserProfile/Account.html", title=current_user.username, form=form
        )
    else:
        return render_template("404/pagenotfound.html", title="Pagenotfound")


@views.route("/Song")
def RecordedSearch():
    return render_template("FoundSong/FoundSong.html")


@views.route("/library", methods=["GET", "POST"])
@login_required
def Library():
    pass
