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
        chal = GenFlagCDBM(
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

    @staticmethod
    def read(challenge, team):
        challenge = GenFlagCDBM.query.filter_by(id=challenge.id).first()
        data = {
            'id': challenge.id,
            'name': challenge.name,
            'value': challenge.value,
            'description': challenge.description,
            'category': challenge.category,
            'hidden': challenge.hidden,
            'max_attempts': challenge.max_attempts,
            'type': challenge.type,
            'type_data': {
                'id': GenFlagCDBM.id,
                'name': GenFlagCDBM.name,
                'templates': GenFlagCDBM.templates,
                'scripts': GenFlagCDBM.scripts,
            }
        }
        return challenge, data

    @staticmethod
    def update(challenge, request):
        challenge = GenFlagCDBM.query.filter_by(id=challenge.id).first()

        challenge.name = request.form['name']
        challenge.description = request.form['description']
        challenge.value = int(request.form.get('value', 0)) if request.form.get('value', 0) else 0
        challenge.max_attempts = int(request.form.get('max_attempts', 0)) if request.form.get('max_attempts', 0) else 0
        challenge.category = request.form['category']
        challenge.hidden = 'hidden' in request.form

        db.session.commit()
        db.session.close()

    @staticmethod
    def delete(challenge):
        WrongKeys.query.filter_by(chalid=challenge.id).delete()
        Solves.query.filter_by(chalid=challenge.id).delete()
        Keys.query.filter_by(chal=challenge.id).delete()
        files = Files.query.filter_by(chal=challenge.id).all()
        for f in files:
            utils.delete_file(f.id)
        Files.query.filter_by(chal=challenge.id).delete()
        Tags.query.filter_by(chal=challenge.id).delete()
        Hints.query.filter_by(chal=challenge.id).delete()
        GenFlagCDBM.query.filter_by(id=challenge.id).delete()
        GenFlagsMap.query.filter_by(id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()

    @staticmethod
    def attempt(chal, request):
        provided_key = request.form['key'].strip()
        chal_keys = GenFlagsMap.query.filter_by(chal=team.id).all()
        for chal_key in chal_keys:
            if get_key_class(chal_key.type).compare(chal_key, provided_key):
                return True, 'Correct'
        return False, 'Incorrect'

    @staticmethod
    def solve(team, chal, request):
        chal = GenFlagCDBM.query.filter_by(id=chal.id).first()
        solve_count = Solves.query.join(Teams, Solves.teamid == Teams.id).filter(Solves.chalid==chal.id, Teams.banned==False).count()

        provided_key = request.form['key'].strip()
        solve = Solves(teamid=team.id, chalid=chal.id, ip=utils.get_ip(req=request), flag=provided_key)
        db.session.add(solve)

        db.session.commit()
        db.session.close()

    @staticmethod
    def fail(team, chal, request):
        provided_key = request.form['key'].strip()
        wrong = WrongKeys(teamid=team.id, chalid=chal.id, ip=utils.get_ip(request), flag=provided_key)
        db.session.add(wrong)
        db.session.commit()
        db.session.close()


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

class GenFlagsMap(db.model):
    id = db.Column(Integer, db.ForeignKey('challenges.id'))
    teamid = db.Column(None, db.ForeignKey('teams.id'), primary_key=True)
    description = db.Column(db.Text)
    flag = db.Column(db.Text)

    def __init__(self, teamid, description, type, flag):
        self.teamid = teamid
        self.flag = flag
        self.type = type
        self.description = description

def load(app):
    app.db.create_all()
    CHALLENGE_CLASSES['genflag'] = GenFlagChallenge
    register_plugin_assets_directory(app, base_path='/plugins/ctfd-generate-flags/assets/')
