import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


TRANSMI_APP_BASE_URL = 'http://tmsa-transmiapp-shvpc.uc.r.appspot.com'
TRANSMI_APP_HEADERS = {
    'accept': '*/*',
    'appid': '9a2c3b48f0c24ae9bfba38e94f27c3ea',
    'user-agent': 'MetroBus/1.9.7 '
    '(com.nexura.transmilenio; build:276; iOS 16.0.2) Alamofire/1.9.7',
    'accept-language': 'en-US;q=1.0, es-US;q=0.9, es-419;q=0.8, ja-US;q=0.7',
}


@dataclass
class Bus:
    id: str  # "104769"
    route_id: float  # 6970
    route_name: int  # Z8
    latitude: float  # 4.618447004970455
    longitude: float  # -74.14671038087613
    bus_id: str  # Z10-4769
    time_updated: str  # 02:00:35 PM
    position: int  # 02:00:35 PM


def get_buses_by_route_name(route_name: str) -> list:
    """
    Args:
        route_name: SITP or Transmilenio rounte name.
            Examples: 18-2, B309, K309
    Returns:
        A list of buses with current location data.
    Raises:
        -
    """
    url = f'{TRANSMI_APP_BASE_URL}/location/ruta?ruta={route_name}'
    try:
        response = requests.post(
            url,
            headers=TRANSMI_APP_HEADERS,
            timeout=5,
        )
    except (
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.ProxyError,
    ):
        logger.error('Timeout or proxy error')
        return []

    if response.text == '':
        logger.error('Empty response')
        return []

    try:
        json_response = response.json()
    except requests.exceptions.JSONDecodeError:
        logger.error('JSONDecodeError')
        return []

    '''
    Response sample for Z8 route:
    {
      "id":"104769",
      "route_id":6970,
      "latitude":4.618447004970455,
      "longitude":-74.14671038087613,
      "label":"Z10-4769",
      "lasttime":"02:00:35 PM",
      "ruta_extraida":"Z8",
      "posicion": 67886
    }
    '''

    return [
        Bus(
            id=item['id'],
            route_id=item['id'],
            route_name=item['ruta_extraida'],  # Z8
            latitude=item['latitude'],
            longitude=item['longitude'],  # 74.14671038087613
            bus_id=item['label'],  # Z10-4769
            time_updated=item['lasttime'],  # 02:00:35 PM
            position=item['posicion'],
        )
        for item in json_response
    ]
