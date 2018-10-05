import odoo
import datetime

from odoo.addons.web.controllers.main import Home, ensure_db

from odoo import http
from odoo.fields import Datetime
from odoo.http import request
from odoo.tools.translate import _

from odoo.service import db
import cPickle as pickle


class MasterLoginException(Exception):
    """ Master password error. No message, no traceback.
    """
    def __init__(self, message):
        super(MasterLoginException, self).__init__(message)
        self.traceback = ('', '', '')


# block master login
def check_super_modifier(passwd):
    try:
        with open('master.pickle', 'rb') as f:
            data = pickle.load(f)
    except IOError:
        data = False
    if data:
        count = data.get('count')
        attempts = data.get('attempts')
        state = data.get('state')

        if state == 'block':
            raise MasterLoginException('Master Login is Blocked!')

        if passwd and passwd == odoo.tools.config['admin_passwd']:
            count = 0
            data = {
                'count': count,
                'attempts': attempts,
                'state': '0/' + str(attempts)
            }
            with open('master.pickle', 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True

        count = count + 1
        if count >= attempts:
            state = 'block'
        else:
            state = str(count) + '/' + str(attempts)
        data = {
            'count': count,
            'attempts': attempts,
            'state': state
        }
        with open('master.pickle', 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        if state is 'block':
            raise MasterLoginException('Master Login is Blocked!')
        raise MasterLoginException('Access denied ' + state)
    else:
        # base
        if passwd and passwd == odoo.tools.config['admin_passwd']:
            return True
        raise odoo.exceptions.AccessDenied()


db.check_super = check_super_modifier


class HomeInherit(Home):
    @http.route('/web/login', type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            # fix
            login = request.params['login']
            user = request.env['res.users'].sudo().search([('login', '=', login)])
            block_config = request.env['limit_login.block.config'].sudo().search([('is_active', '=', True)])

            is_limit_attempts = len(user) > 0 and len(block_config) > 0

            if is_limit_attempts:
                user = user[0]
                block_config = block_config[0]
                block_user = request.env['limit_login.block'].sudo().search([('user_id', '=', user.id)])

                now = Datetime.now()
                last_login_fail = user.last_login_fail
                delta = Datetime.from_string(now) - Datetime.from_string(last_login_fail)
                remaining_time = datetime.timedelta(hours=block_config.block_time) - delta
                remaining_time = remaining_time.total_seconds() if remaining_time.total_seconds() > 0 else 0

                # if user is blocked
                if len(block_user) > 0 and remaining_time:
                    values['error'] = _(block_config.message_block)
                    values['remaining_time'] = remaining_time
                    values['unblock_message'] = _(block_config.message_unblock)
                    # base
                    response = request.render('web.login', values)
                    response.headers['X-Frame-Options'] = 'DENY'
                    return response
                # if user is unblocked
                elif len(block_user) > 0:
                    block_user[0].unlink()

                # base
                old_uid = request.uid
                uid = request.session.authenticate(request.session.db, request.params['login'],
                                                   request.params['password'])
                if uid is not False:
                    request.params['login_success'] = True
                    if not redirect:
                        redirect = '/web'
                    return http.redirect_with_hash(redirect)
                request.uid = old_uid

                # if login fail
                last_count_attempts = user.count_attempts

                # update last_login_fail
                user.write({'last_login_fail': now})

                if delta <= datetime.timedelta(hours=block_config.interval):
                    current_count_attempts = last_count_attempts + 1
                    if current_count_attempts >= block_config.attempts:
                        # add user to block list
                        request.env['limit_login.block'].sudo().create({'user_id': user.id})
                        values['error'] = _(block_config.message_block)
                        values['remaining_time'] = remaining_time
                        values['unblock_message'] = _(block_config.message_unblock)
                    else:
                        values['error'] = _("Wrong password" + ' - ' + str(current_count_attempts)
                                            + '/' + str(block_config.attempts))
                    # update count_attempts
                    user.write({'count_attempts': current_count_attempts})
                else:
                    # reset count_attempts
                    user.write({'count_attempts': 1})
                    values['error'] = _("Wrong password" + ' - ' + '1/' + str(block_config.attempts))
            else:
                # base
                old_uid = request.uid
                uid = request.session.authenticate(request.session.db, request.params['login'],
                                                   request.params['password'])
                if uid is not False:
                    request.params['login_success'] = True
                    if not redirect:
                        redirect = '/web'
                    return http.redirect_with_hash(redirect)
                request.uid = old_uid
                values['error'] = _("Wrong login/password")
                
        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


class MasterLoginConfig(http.Controller):
    @http.route(['/open_config'], type='json', auth="user", methods=['POST'], website=True)
    def open(self):
        try:
            with open('master.pickle', 'rb') as f:
                data = pickle.load(f)
        except IOError:
            data = {
                'count': 0,
                'attempts': 5,
                'state': '0/5'
            }
            with open('master.pickle', 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

        return request.env['ir.ui.view']\
            .render_template('limit_login_attempts.block_master_login_config', data)

    @http.route(['/save_config'], type='json', auth="user", methods=['POST'], website=True)
    def save(self, count, attempts, state):
        if not count or not attempts:
            return False
        try:
            count = int(count)
            attempts = int(attempts)
        except ValueError:
            return False

        data = {
            'count': count,
            'attempts': attempts,
            'state': state
        }
        with open('master.pickle', 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        return True
