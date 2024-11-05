{
    'name': 'Entrega Integración Logistica',
    'version': '17.0',
    'summary': 'Integración de métodos de envío con Entregar API',
    'description': 'Módulo personalizado para integrar los métodos de envío de Entregar en Odoo 17.',
    'author': 'Sebastián Díaz y Agostina Salas',
    'depends': ['base', 'delivery', 'sale'],
    'data': [
        'views/delivery_carrier_views.xml'
    ],
    'installable': True,
    'application': False,
}

