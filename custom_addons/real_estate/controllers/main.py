from odoo import http
from odoo.http import request

class RealEstateApi(http.Controller):

    def _error(self, code, message, status):
        return request.make_json_response(
            {'error': code, 'message': message},status=status,
        )

    def _require_login(self):
        if request.env.user._is_public():
            return self._error('unauthorized','login required',401)
        return None

    def _serialize_property(self, prop):
        return {
            'id': prop.id,
            'code': prop.code,
            'name': prop.name,
            'state': prop.state,
            'expected_price': prop.expected_price,
            'bedrooms': prop.bedrooms,
            'postcode': prop.postcode or None,
            'type': prop.type_id.name or None,
            'tags': prop.tag_ids.mapped('name'),
            'date_availability': (
                prop.date_availability.isoformat() if prop.date_availability else None
            ),
    }

    @http.route('/real_estate/api/properties', type='http',auth='public',methods=['GET'])
    def list_properties(self, **params):
        denied = self._require_login()
        if denied:
            return denied

        try:
            limit = max(1, min(int(params.get('limit', 20)), 100))
            offset = max(0, int(params.get('offset', 0)))
        except ValueError:
            return self._error('bad_request', 'limit and offset must be integers', 400)
        
        domain = []
        if params.get('state'):
            domain.append(('state', '=', params['state']))
        if params.get('postcode'):
            domain.append(('postcode', '=', params['postcode']))

        Property = request.env['real.estate.property']
        total = Property.search_count(domain)
        records = Property.search(domain, limit=limit, offset=offset, order='id')

        return request.make_json_response({
            'total': total,
            'limit': limit,
            'offset': offset,
            'records': [self._serialize_property(p) for p in records],
        })