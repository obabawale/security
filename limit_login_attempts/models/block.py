import datetime

from odoo import api, fields, models, _


class BlockConfig(models.Model):
    _name = 'limit_login.block.config'

    name = fields.Char(string='Name')
    attempts = fields.Integer(string='Attempts', default=5, required=True)
    block_time = fields.Float(string='Block Time', default=0.083333333, required=True)
    interval = fields.Float(string='Interval', default=0.016666667, required=True)
    message_block = fields.Text(string='Block Message', default='Your account is blocked!')
    message_unblock = fields.Text(string='Unblock Message', default='You can login now!')
    is_active = fields.Boolean(string='Active', default=False)

    @api.multi
    def write(self, vals):
        if vals.get('is_active'):
            inactive = self.search([('is_active', '=', True)])
            inactive.write({'is_active': False})
        return super(BlockConfig, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('is_active'):
            inactive = self.search([('is_active', '=', True)])
            inactive.write({'is_active': False})
        return super(BlockConfig, self).create(vals)


class Block(models.Model):
    _name = 'limit_login.block'
    _sql_constraints = [('user_unique', 'unique(user_id)', 'User already blocked!')]

    user_id = fields.Many2one('res.users', string='User')
    remaining_time = fields.Char(string='Remaining Time', compute='_compute_remaining_time')
    last_login_fail = fields.Datetime(related='user_id.last_login_fail', string='Last Login Fail')

    def _compute_remaining_time(self):
        block_config = self.env['limit_login.block.config'].search([('is_active', '=', True)])
        if len(block_config) > 0:
            block_config = block_config[0]
            for block in self:
                delta = datetime.datetime.now() - fields.Datetime.from_string(block.last_login_fail)
                remaining_time = datetime.timedelta(hours=block_config.block_time) - delta
                remaining_time = remaining_time if remaining_time.total_seconds() > 0 else datetime.timedelta(microseconds=0)
                block.remaining_time = remaining_time - datetime.timedelta(microseconds=remaining_time.microseconds)


class User(models.Model):
    _inherit = 'res.users'

    count_attempts = fields.Integer(default=0)
    last_login_fail = fields.Datetime(default=lambda self: fields.Datetime.now())


class BlockMasterLogin(models.TransientModel):
    _name = 'limit_login.block.master'
