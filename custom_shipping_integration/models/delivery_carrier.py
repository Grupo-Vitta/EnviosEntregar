from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)

class EntregarShippingCarrier(models.Model):
    _inherit = 'delivery.carrier'

    api_token = fields.Char(string="API Token")
    token_timestamp = fields.Datetime(string="Token Timestamp")

    def _authenticate_api(self):
        url = "https://homologacion.entregarweb.com/api/v1/auth/token"
        headers = {'Content-type': 'application/json'}
        payload = {
            'client_api': 'a84e0675aba4322fbebd4ccf164f238deb9ea501b6ac15f16ae4c6aacf590426',
            'client_secret': 'cb4979d3152ee649fb7f94b3ba4ac2625baa803d1ae43e0b7642b6b105b78758'
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            token = response.json().get('access_token')
            self.api_token = token
            self.token_timestamp = fields.Datetime.now()
            return token
        else:
            _logger.error(f"Failed to authenticate API: {response.status_code} - {response.text}")
            return None

    def _get_valid_token(self):
        if not self.api_token or not self.token_timestamp or (fields.Datetime.now() - self.token_timestamp).total_seconds() > 6 * 3600:
            return self._authenticate_api()
        return self.api_token

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
            _logger.error(f"Failed to create shipping: {response.status_code} - {response.text}")
            return None

    def action_confirm(self):
        res = super(EntregarShippingCarrier, self).action_confirm()

        if self.delivery_method_id.name == 'Método de Envío Externo':
            items = [{"quantity": 3, "weight": 100.0, "width": 200.0, "height": 30.4}]
            shipping_data = self._create_shipping(
                receives=self.partner_id.name,
                address=self.partner_id.street,
                location=self.partner_id.city,
                postal_code=self.partner_id.zip,
                items=items,
                email=self.partner_id.email,
                references=self.partner_id.street2
            )
            if shipping_data:
                _logger.info(f"Shipping created successfully: {shipping_data}")

        return res
