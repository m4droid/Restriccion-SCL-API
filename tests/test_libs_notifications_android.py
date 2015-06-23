from mock import Mock, patch
import moment

from .base_tests import BaseTestCase
from restriccion_scl.libs.notifications import send_to_android_devices


class TestLibsNotifications(BaseTestCase):

    @patch('restriccion_scl.libs.notifications.GCM')
    def test_libs_notifications_send_to_android_devices_empty_response(self, mock_gcm):
        mock_method = Mock()
        mock_method.json_request = Mock(return_value={})

        mock_gcm.side_effect = lambda *a, **ka: mock_method

        send_to_android_devices(['fake_gcm_id'], {'payload': 'asdf'})


    @patch('restriccion_scl.libs.notifications.moment.now')
    @patch('restriccion_scl.libs.notifications.GCM')
    def test_libs_notifications_send_to_android_unregistered_or_invalid_devices(self, mock_gcm, mock_moment):
        mock_datetime = moment.date('2015-06-22', '%Y-%m-%d')
        mock_moment.side_effect = lambda: mock_datetime

        mock_method = Mock()
        mock_method.json_request = Mock(return_value={
            'errors': {
                'NotRegistered': ['gcm_not_registered'],
                'InvalidRegistration': ['gcm_invalid_registration']
            }
        })

        mock_gcm.side_effect = lambda *a, **ka: mock_method

        device_to_remain_data = {'tipo': 'android', 'id': 'gcm_to_remain', 'fecha_registro': mock_datetime.isoformat()}

        self.mongo_db.devices.insert_one({
            'tipo': 'android',
            'id': 'gcm_not_registered',
            'fecha_registro': mock_datetime.isoformat()
        })
        self.mongo_db.devices.insert_one({
            'tipo': 'android',
            'id': 'gcm_invalid_registration',
            'fecha_registro': mock_datetime.isoformat()
        })
        self.mongo_db.devices.insert_one(device_to_remain_data)
        self.assertEqual(3, self.mongo_db.devices.count())

        send_to_android_devices(['fake_gcm_id'], {'payload': 'asdf'})
        self.assertEqual(1, self.mongo_db.devices.count())
        self.assertEqual(
            0,
            self.mongo_db.devices.find({
                'tipo': 'android',
                'id': {'$in': ['gcm_not_registered', 'gcm_invalid_registration']}
            }).count()
        )        

        device_to_remain = self.mongo_db.devices.find_one({})
        self.assertEqual(device_to_remain_data, device_to_remain)

    @patch('restriccion_scl.libs.notifications.moment.now')
    @patch('restriccion_scl.libs.notifications.GCM')
    def test_libs_notifications_send_to_android_receiving_canonical_ids_response(self, mock_gcm, mock_moment):
        mock_datetime = moment.date('2015-06-22', '%Y-%m-%d')
        mock_moment.side_effect = lambda: mock_datetime

        mock_method = Mock()
        mock_method.json_request = Mock(return_value={
            'canonical': {
                'gcm_id_to_remove': 'gcm_to_remain_3',
            }
        })

        mock_gcm.side_effect = lambda *a, **ka: mock_method

        device_to_remain_1_data = {'tipo': 'android', 'id': 'gcm_to_remain_1', 'fecha_registro': mock_datetime.isoformat()}
        device_to_remain_2_data = {'tipo': 'android', 'id': 'gcm_to_remain_2', 'fecha_registro': mock_datetime.isoformat()}

        self.mongo_db.devices.insert_one({'tipo': 'android', 'id': 'gcm_id_to_remove', 'fecha_registro': mock_datetime.isoformat()})
        self.mongo_db.devices.insert_one(device_to_remain_1_data)
        self.mongo_db.devices.insert_one(device_to_remain_2_data)
        self.assertEqual(3, self.mongo_db.devices.count())

        send_to_android_devices(['fake_gcm_id'], {'payload': 'asdf'})
        self.assertEqual(3, self.mongo_db.devices.count())

        self.assertEqual(0, self.mongo_db.devices.find({'tipo': 'android', 'id': 'gcm_id_to_remove'}).count())        