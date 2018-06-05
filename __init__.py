from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import BaseChallenge, CHALLENGE_CLASSES
from CTFd.plugins.keys import get_key_class
from CTFd.models import db, Solves, WrongKeys, Keys, Challenges, Files, Tags, Teams, Hints
import random
import string

class GenFlagChallenge(BaseChallenge):
    id = "genflag"
    name = "genflag"

    @staticmethod
    def create(request):
        files = request.files.getlist('files[]')

        # Create challenge
        chal = GenFlags(
            name=request.form['name'],
            value=request.form['value'],
            category=request.form['category'],
            type=request.form['chaltype'],
            generator=request.form['generator']
        )

        if 'hidden' in request.form:
            chal.hidden = True
        else:
            chal.hidden = False

        max_attempts = request.form.get('max_attempts')
        if max_attempts and max_attempts.isdigit():
            chal.max_attempts = int(max_attempts)

        gen = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
        chal.key = "generated_flag_" + gen

        db.session.add(chal)
        db.session.commit()

        flag = Keys(chal.id, chal.key, 'static')
        db.session.add(flag)
        db.session.commit()

        for f in files:
            utils.upload_file(file=f, chalid=chal.id)

        db.session.commit()


class GenFlagCDBM(challenges):
    __mapper_args__ = {'polymorphic_identity': 'genflags'}
    id = db.Column(None, db.ForeignKey('challenges.id'), primary_key=True)
    key = db.Column(db.Text)
    generator = db.Column(db.Text)

    def __init__(self, name, value, category, type='genflag', key, generator):
        self.name = name
        self.value = value
        self.category = category
        self.type = type
        self.key = key
        self.generator = generator

class GenFlags(db.model):
    id = db.Column(Integer, db.ForeignKey('challenges.id'))
    teamid = db.Column(None, db.ForeignKey('teams.id'), primary_key=True)
    description = db.Column(db.Text)
    flag = db.Column(db.Text)

    def __init__(self, teamid, description, flag):
        self.teamid = teamid
        self.flag = flag
        self.description = description

def load(app):
    app.db.create_all()
    CHALLENGE_CLASSES['genflag'] = GenFlagChallenge
    register_plugin_assets_directory(app, base_path='/plugins/ctfd-generate-flags/assets/')
