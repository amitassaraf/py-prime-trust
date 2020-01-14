import os
from decimal import Decimal
from typing import Tuple
from urllib.parse import urljoin
from uuid import uuid4

import ujson
from box import Box
from requests import Session, Response

from .consts import BASE_API_URL, PRODUCTION_ENV, SANDBOX_ENV
from .models import *
from .utils import require_connection


class PrimeURLs:
    JWT_AUTH = '/auth/jwts'
    CUSTODY_AGREEMENT_PREVIEW = 'agreement-previews'
    CUSTODY_ACCOUNT = 'accounts'
    CONTACTS = 'contacts'
    FUND_TRANSFER = 'funds-transfers'
    FUND_TRANSFER_METHODS = 'funds-transfer-methods'
    CONTRIBUTIONS = 'contributions'
    DISBURSEMENTS = 'disbursements'
    ACCOUNT_CASH_TRANSFERS = 'account-cash-transfers'
    USERS = 'users'
    DOCUMENTS = 'uploaded-documents'
    KYC_DOCUMENT_CHECKS = 'kyc-document-checks'


class PrimeClient(Session):
    API_VERSION = 'v2'

    def __init__(self, root_user_email: str, root_user_password: str, debug: bool = False):
        super(PrimeClient, self).__init__()
        self._environment = SANDBOX_ENV if debug else PRODUCTION_ENV
        self._base_url = BASE_API_URL.format(env=self._environment)
        self._root_user_email = root_user_email
        self._root_user_password = root_user_password
        self._auth_token = None

    def request(self, method, url, *args, **kwargs) -> Tuple[Box, Response]:
        url = urljoin(self._base_url, f'/{self.API_VERSION}', f'{url}')
        if method == 'POST':
            self.headers.update({'X-Request-ID': uuid4().hex})
        response = super(PrimeClient, self).request(method, url, *args, **kwargs)
        return Box(response.json()), response

    def create_api_user(self, name: str, email: str, password: str) -> bool:
        data, http_response = self.post(PrimeURLs.USERS, data=ujson.dumps(RootDataNode(data=DataNode(
            type="user",
            attributes={
                "email": email,
                "name": name,
                "password": password,
            }
        )).to_json()))
        return data

    def connect(self) -> bool:
        data, http_response = self.post(PrimeURLs.JWT_AUTH, auth=(self._root_user_email, self._root_user_password))
        self._auth_token = data.token
        self.headers.update({'Authorization': f'Bearer {self._auth_token}'})
        return True

    @require_connection
    def custody_account_agreement_preview(self, contact: Contact) -> DataNode:
        data, http_response = self.post(PrimeURLs.CUSTODY_AGREEMENT_PREVIEW,
                                        data=ujson.dumps(RootDataNode(
                                            data=DataNode(
                                                type="account",
                                                attributes={
                                                    "account-type": "custodial",
                                                    "name": f'{contact.name}\'s Account',
                                                    "authorized-signature": f'{contact.name}',
                                                    "owner": contact.to_json()
                                                }
                                            )
                                        ).to_json()))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_account_create(self, contact: Contact) -> DataNode:
        data, http_response = self.post(PrimeURLs.CUSTODY_ACCOUNT,
                                        data=ujson.dumps(RootDataNode(
                                            data=DataNode(
                                                type="account",
                                                attributes={
                                                    "account-type": "custodial",
                                                    "name": f'{contact.name}\'s Account',
                                                    "authorized-signature": f'{contact.name}',
                                                    "owner": contact.to_json()
                                                }
                                            )
                                        ).to_json()))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_account_create_entity(self, contact: Contact) -> DataNode:
        data, http_response = self.post(PrimeURLs.CUSTODY_ACCOUNT,
                                        data=ujson.dumps(RootDataNode(
                                            data=DataNode(
                                                type="account",
                                                attributes={
                                                    "account-type": "custodial",
                                                    "name": f'{contact.name}\'s Account',
                                                    "authorized-signature": f'{contact.related_contacts[0].name}',
                                                    "owner": contact.to_json()
                                                }
                                            )
                                        ).to_json()))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_account_activate(self, custody_account_id: str) -> DataNode:
        data, http_response = self.post(
            urljoin(PrimeURLs.CUSTODY_ACCOUNT, f'/{custody_account_id}', f'/{self._environment}', f'/open'))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_kyc_start_process(self, custody_account_id: str, contact: Contact) -> DataNode:
        data, http_response = self.post(PrimeURLs.CONTACTS,
                                        data=ujson.dumps(RootDataNode(
                                            data=DataNode(
                                                type="contacts",
                                                attributes={
                                                    "account-id": custody_account_id,
                                                    **contact.to_json()
                                                }
                                            )
                                        ).to_json()))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_kyc_get_status(self, contact_id: str) -> RootListDataNode:
        data, http_response = self.get(PrimeURLs.CONTACTS,
                                       params={
                                           'filter[contact.id eq]': contact_id,
                                           'include': 'cip-checks,aml-checks,kyc-document-checks'
                                       })
        return RootListDataNode.from_json(data.to_dict())

    @require_connection
    def fund_transfer_method_add(self, contact_id: str, transfer_method: FundTransferMethod) -> DataNode:
        data, http_response = self.post(PrimeURLs.FUND_TRANSFER_METHODS,
                                        data=ujson.dumps(RootDataNode(
                                            data=DataNode(
                                                type="funds-transfer-methods",
                                                attributes={
                                                    "contact-id": contact_id,
                                                    **transfer_method.to_json()
                                                }
                                            )
                                        ).to_json()))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_deposit(self, custody_account_id: str, contact_id: str, fund_transfer_method_id: str,
                              amount: Decimal) -> DataNode:
        data, http_response = self.post(
            PrimeURLs.CONTRIBUTIONS,
            params={'include': 'funds-transfer'},
            data=ujson.dumps(RootDataNode(
                data=DataNode(
                    type="contributions",
                    attributes={
                        "amount": amount,
                        "funds-transfer-method-id": fund_transfer_method_id,
                        "account-id": custody_account_id,
                        "contact-id": contact_id
                    }
                )
            ).to_json()))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_withdraw(self, custody_account_id: str, amount: Decimal) -> DataNode:
        data, http_response = self.post(
            PrimeURLs.DISBURSEMENTS,
            params={'include': 'funds-transfer,disbursement-authorization'},
            data=ujson.dumps(RootDataNode(
                data=DataNode(
                    type="disbursements",
                    attributes={
                        "amount": amount,
                        "account-id": custody_account_id
                    }
                )
            ).to_json()))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_custody_to_custody(self, from_custody_account_id: str, to_custody_account_id: str,
                                         amount: Decimal) -> DataNode:
        data, http_response = self.post(
            PrimeURLs.ACCOUNT_CASH_TRANSFERS,
            params={'include': 'from-account-cash-totals,to-account-cash-totals'},
            data=ujson.dumps(RootDataNode(
                data=DataNode(
                    type="account-cash-transfers",
                    attributes={
                        "amount": amount,
                        "from-account-id": from_custody_account_id,
                        "to-account-id": to_custody_account_id
                    }
                )
            ).to_json()))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_get_status(self, funds_transfer_id: str) -> DataNode:
        data, http_response = self.get(PrimeURLs.FUND_TRANSFER,
                                       params={
                                           'filter[id eq]': funds_transfer_id,
                                           'include': 'contingent-holds'
                                       })
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_account_upload_document(self, contact_id: str, document_label: str,
                                        file_path: str, public: bool = False) -> DataNode:
        data, http_response = self.post(
            PrimeURLs.DOCUMENTS,
            files=(
                ('contact-id', (None, contact_id)),
                ('label', (None, document_label)),
                ('public', (None, public)),
                ('file', (os.path.basename(file_path), open(file_path, 'rb'))),
            ))
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_account_kyc_document_uploaded(self, contact_id: str, uploaded_document_id: str,
                                              expires_on: str, identity: bool, identity_photo: bool,
                                              proof_of_address: bool, document_type: str,
                                              backside_document_id: str = None) -> DataNode:
        data, http_response = self.post(
            PrimeURLs.KYC_DOCUMENT_CHECKS,
            data=ujson.dumps(RootDataNode(
                data=DataNode(
                    type="kyc-document-checks",
                    attributes={
                        "contact-id": contact_id,
                        "uploaded-document-id": uploaded_document_id,
                        "backside-document-id": backside_document_id,
                        "expires-on": expires_on,
                        "identity": identity,
                        "identity-photo": identity_photo,
                        "proof-of-address": proof_of_address,
                        "kyc-document-type": document_type,
                        "kyc-document-country": "US",
                    }
                )
            ).to_json()))
        return DataNode.from_json(data.data.to_dict())
