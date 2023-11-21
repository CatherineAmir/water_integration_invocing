# -*- coding: utf-8 -*-
# from odoo import http


# class MenofiaIntegrationFiles(http.Controller):
#     @http.route('/menofia_integration_files/menofia_integration_files/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/menofia_integration_files/menofia_integration_files/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('menofia_integration_files.listing', {
#             'root': '/menofia_integration_files/menofia_integration_files',
#             'objects': http.request.env['menofia_integration_files.menofia_integration_files'].search([]),
#         })

#     @http.route('/menofia_integration_files/menofia_integration_files/objects/<model("menofia_integration_files.menofia_integration_files"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('menofia_integration_files.object', {
#             'object': obj
#         })
