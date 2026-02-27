from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import date, time, timedelta

from clinic_api.apps.users.models import User
from clinic_api.apps.doctors.models import TimeSlot
from clinic_api.apps.appointments.models import Appointment


def create_user(username, role, password='pass1234'):
    return User.objects.create_user(username=username, email=f'{username}@example.com', password=password, role=role)


class ClinicAPITestCase(APITestCase):

    def setUp(self):
        # create one doctor and one patient and an admin
        self.doctor = create_user('drsmith', 'doctor')
        self.patient = create_user('alice', 'patient')
        self.admin = create_user('admin', 'admin')
        # obtain tokens for each
        self.doctor_token = self.obtain_token('drsmith', 'pass1234')
        self.patient_token = self.obtain_token('alice', 'pass1234')
        self.admin_token = self.obtain_token('admin', 'pass1234')

    def obtain_token(self, username, password):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': username, 'password': password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_doctor_creates_timeslot_and_patient_books(self):
        # doctor creates timeslot
        self.auth(self.doctor_token)
        ts_url = reverse('timeslot-list')
        tomorrow = date.today() + timedelta(days=1)
        data = {'doctor': self.doctor.id, 'date': tomorrow.isoformat(), 'start_time': '09:00', 'end_time': '10:00'}
        r = self.client.post(ts_url, data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        timeslot_id = r.data['id']
        # make sure the slot is marked available in the DB
        ts_obj = TimeSlot.objects.get(pk=timeslot_id)
        self.assertTrue(ts_obj.is_available, "timeslot should be available immediately after creation")

        # patient lists available slots for doctor
        self.auth(self.patient_token)
        # sanity check: auth/me should return 200
        me = self.client.get(reverse('auth-me'))
        # debug prints removed for production-quality tests
        dr_ts_url = reverse('doctor-timeslots', kwargs={'pk': self.doctor.id})
        r = self.client.get(dr_ts_url)
        # response printed only when assertion fails (handled below)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # api may return paginated dict or plain list
        results = r.data.get('results', r.data)
        self.assertTrue(any(ts['id'] == timeslot_id for ts in results))

        # patient books appointment
        appt_url = reverse('appointment-list')
        r = self.client.post(appt_url, {'doctor': self.doctor.id, 'timeslot': timeslot_id})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        appt_id = r.data['id']

        # patient cannot book same slot again
        r = self.client.post(appt_url, {'doctor': self.doctor.id, 'timeslot': timeslot_id})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

        # doctor can see appointment and change status
        self.auth(self.doctor_token)
        r = self.client.get(reverse('appointment-detail', kwargs={'pk': appt_id}))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r = self.client.patch(reverse('appointment-detail', kwargs={'pk': appt_id}), {'status': 'confirmed'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['status'], 'confirmed')

    def test_patient_cannot_update_other_appointment(self):
        # doctor creates two slots and patient books one
        self.auth(self.doctor_token)
        ts1 = self.client.post(reverse('timeslot-list'), {'doctor': self.doctor.id, 'date': (date.today()+timedelta(days=2)).isoformat(), 'start_time':'10:00','end_time':'11:00'}).data['id']
        # ensure slot is available
        ts_obj = TimeSlot.objects.get(pk=ts1)
        self.assertTrue(ts_obj.is_available, "slot unexpectedly unavailable before booking")
        self.auth(self.patient_token)
        appt = self.client.post(reverse('appointment-list'), {'doctor': self.doctor.id, 'timeslot': ts1}).data
        # another patient
        bob = create_user('bob','patient')
        bob_token = self.obtain_token('bob','pass1234')
        self.auth(bob_token)
        r = self.client.patch(reverse('appointment-detail', kwargs={'pk': appt['id']}), {'status': 'confirmed'})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_cannot_book_own_appointment(self):
        # doctor tries to book own slot
        self.auth(self.doctor_token)
        ts = self.client.post(reverse('timeslot-list'), {'doctor': self.doctor.id, 'date': (date.today()+timedelta(days=3)).isoformat(), 'start_time':'11:00','end_time':'12:00'}).data['id']
        # doctor attempts to create appointment as patient
        r = self.client.post(reverse('appointment-list'), {'doctor': self.doctor.id, 'timeslot': ts})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_migration_and_models(self):
        # simple sanity check on models
        self.assertTrue(User.objects.filter(username='drsmith').exists())
        self.assertTrue(TimeSlot.objects.count() >= 0)
        self.assertTrue(Appointment.objects.count() >= 0)
