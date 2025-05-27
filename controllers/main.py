from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound  # ou Forbidden

class SignupDisabled(http.Controller):

    @http.route('/web/signup', type='http', auth='public', website=True)
    def disable_signup(self, **kwargs):
        # Option 1 : renvoyer une erreur 404
        print("TEST NotFound")
        raise NotFound()

        # Option 2 : rediriger vers la page de login
        # return request.redirect('/web/login')
