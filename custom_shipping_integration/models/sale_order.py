import requests
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    api_token = fields.Char(string="API Token")
    token_exp = fields.Datetime(string="Token Expiration")

    def _authenticate_api(self):
        url = "https://homologacion.entregarweb.com/api/v1/auth/token"
        headers = {'Content-type': 'multipart/form-data; boundary=wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'}
        payload = {
            'client_api': 'a84e0675aba4322fbebd4ccf164f238deb9ea501b6ac15f16ae4c6aacf590426',
            'client_secret': 'cb4979d3152ee649fb7f94b3ba4ac2625baa803d1ae43e0b7642b6b105b78758'
        }

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            token = response.json().get('access_token')
            self.api_token = token
            self.token_exp = fields.Datetime.now()
            return token
        else:
            _logger.error("Failed to authenticate API")
            return None

    def is_token_exp(self):
        if not self.token_exp: #si token_exp no tiene valor o no existe, retorna verdadero (como caducado)
            return True
        return fields.Datetime.now() >= self.token_exp
        
    def _get_valid_token(self):
        if not self.is_token_exp():
            return self.api_token
        return self._authenticate_api()

    def _create_shipping(self, receives, address, location, postal_code, items, email=None, references=None):
        url = "https://homologacion.entregarweb.com/api/v1/shipping/new"
        headers = {'Authorization': f'Bearer {self._get_valid_token()}'}
        
        payload = {
            'receives': receives,
            'address': address,
            'location': location,
            'postal_code': postal_code,
            'items': items
        }

        if email:
            payload['email'] = email
        if references:
            payload['references'] = references

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            _logger.error("Failed to create shipping")
            return None

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        if self.delivery_method_id.name == 'Método de Envío Externo':
            items = "[\"3,100.0,200.0,30.4\"]"
            shipping_data = self._create_shipping(
                receives=self.partner_id.name,
                address=self.partner_id.street,
                location=self.partner_id.city,
                postal_code=self.partner_id.zip,
                items=items,
                email=self.partner_id.email,
                references=self.partner_id.street2  # Cambia `street2` si tienes otro campo para referencias
            )
            if shipping_data:
                _logger.info(f"Shipping created successfully: {shipping_data}")

        return res
