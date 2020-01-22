import os
from decimal import Decimal
from typing import Tuple
from urllib.parse import urljoin
from uuid import uuid4

import requests
import ujson
from box import Box, BoxList
from requests import Session, Response
from simplejson.errors import JSONDecodeError

from .consts import BASE_API_URL, PRODUCTION_ENV, SANDBOX_ENV
from .exceptions import PrimeTrustError
from .models import *
from .utils import require_connection


class PrimeTypes:
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
    CIP_CHECKS = 'cip-checks'
    WEBHOOK_CONFIGS = 'webhook-configs'
    WEBHOOKS = 'webhooks'
    CONTINGENT_HOLDS = 'contingent-holds'
    ACCOUNT_CASH_TOTALS = 'account-cash-totals'
    DISBURSEMENTS_AUTH = 'disbursement-authorizations'


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
        url = urljoin(self._base_url, os.path.join(f'{self.API_VERSION}', f'{url}'))
        if method == 'POST':
            self.headers.update({'X-Request-ID': uuid4().hex})
        response = super(PrimeClient, self).request(method, url, *args, **kwargs)
        try:
            return Box(response.json()), response
        except JSONDecodeError:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                raise PrimeTrustError(str(err), {})

    def create_api_user(self, name: str, email: str, password: str) -> bool:
        data, http_response = self.post(PrimeTypes.USERS, data=ujson.dumps(RootDataNode(data=DataNode(
            type="user",
            attributes={
                "email": email,
                "name": name,
                "password": password,
            }
        )).to_json()))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return data

    def connect(self) -> bool:
        data, http_response = self.post(PrimeTypes.JWT_AUTH, auth=(self._root_user_email, self._root_user_password))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        self._auth_token = data.token
        self.headers.update({'Authorization': f'Bearer {self._auth_token}'})
        return True

    @require_connection
    def custody_account_agreement_preview(self, contact: Contact) -> DataNode:
        data, http_response = self.post(PrimeTypes.CUSTODY_AGREEMENT_PREVIEW,
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
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_account_create(self, contact: Contact) -> DataNode:
        data, http_response = self.post(PrimeTypes.CUSTODY_ACCOUNT,
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
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_account_create_entity(self, contact: Contact) -> DataNode:
        data, http_response = self.post(PrimeTypes.CUSTODY_ACCOUNT,
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
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_custody_account_activate(self, custody_account_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.CUSTODY_ACCOUNT, f'{custody_account_id}', f'{self._environment}', 'open'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_kyc_start_process(self, custody_account_id: str, contact: Contact) -> DataNode:
        data, http_response = self.post(PrimeTypes.CONTACTS,
                                        data=ujson.dumps(RootDataNode(
                                            data=DataNode(
                                                type="contacts",
                                                attributes={
                                                    "account-id": custody_account_id,
                                                    **contact.to_json()
                                                }
                                            )
                                        ).to_json()))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_kyc_update(self, contact_id: str, contact: Contact) -> DataNode:
        data, http_response = self.patch(os.path.join(PrimeTypes.CONTACTS, f'{contact_id}'),
                                         data=ujson.dumps(RootDataNode(
                                             data=DataNode(
                                                 type="contacts",
                                                 attributes={
                                                     **contact.to_json()
                                                 }
                                             )
                                         ).to_json()))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_kyc_get_status(self, contact_id: str) -> RootListDataNode:
        data, http_response = self.get(PrimeTypes.CONTACTS,
                                       params={
                                           'filter[id eq]': contact_id,
                                           'include': 'cip-checks,kyc-document-checks'
                                       })
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return RootListDataNode.from_json(data.to_dict())

    @require_connection
    def fund_transfer_method_add(self, contact_id: str, transfer_method: FundTransferMethod) -> DataNode:
        data, http_response = self.post(PrimeTypes.FUND_TRANSFER_METHODS,
                                        data=ujson.dumps(RootDataNode(
                                            data=DataNode(
                                                type="funds-transfer-methods",
                                                attributes={
                                                    "contact-id": contact_id,
                                                    **transfer_method.to_json()
                                                }
                                            )
                                        ).to_json()))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_method_remove(self, fund_transfer_method_id: str) -> DataNode:
        data, http_response = self.delete(os.path.join(PrimeTypes.FUND_TRANSFER_METHODS, f'{fund_transfer_method_id}'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_cancel(self, fund_transfer_id: str) -> DataNode:
        data, http_response = self.post(os.path.join(PrimeTypes.FUND_TRANSFER, f'{fund_transfer_id}', 'cancel'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_deposit(self, custody_account_id: str, contact_id: str, fund_transfer_method_id: str,
                              amount: Decimal) -> DataNode:
        data, http_response = self.post(
            PrimeTypes.CONTRIBUTIONS,
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
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_withdraw(self, custody_account_id: str, contact_id: str, fund_transfer_method_id: str,
                               amount: Decimal) -> DataNode:
        data, http_response = self.post(
            PrimeTypes.DISBURSEMENTS,
            params={'include': 'funds-transfer'},
            data=ujson.dumps(RootDataNode(
                data=DataNode(
                    type="disbursements",
                    attributes={
                        "amount": amount,
                        "funds-transfer-method-id": fund_transfer_method_id,
                        "account-id": custody_account_id,
                        "contact-id": contact_id
                    }
                )
            ).to_json()))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_custody_to_custody(self, from_custody_account_id: str, to_custody_account_id: str,
                                         amount: Decimal) -> DataNode:
        data, http_response = self.post(
            PrimeTypes.ACCOUNT_CASH_TRANSFERS,
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
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def fund_transfer_get_status(self, funds_transfer_id: str) -> RootListDataNode:
        data, http_response = self.get(PrimeTypes.FUND_TRANSFER,
                                       params={
                                           'filter[id eq]': funds_transfer_id,
                                           'include': 'contingent-holds'
                                       })
        if not isinstance(data, BoxList) and 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return RootListDataNode.from_json(data.to_dict())

    @require_connection
    def custody_account_upload_document(self, contact_id: str, document_label: str,
                                        file_path: str, public: bool = False) -> DataNode:
        data, http_response = self.post(
            PrimeTypes.DOCUMENTS,
            files=(
                ('contact-id', (None, contact_id)),
                ('label', (None, document_label)),
                ('public', (None, public)),
                ('file', (os.path.basename(file_path), open(file_path, 'rb'))),
            ))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def custody_account_kyc_document_uploaded(self, document: KYCDocument) -> DataNode:
        data, http_response = self.post(
            PrimeTypes.KYC_DOCUMENT_CHECKS,
            data=ujson.dumps(RootDataNode(
                data=DataNode(
                    type="kyc-document-checks",
                    attributes={
                        **document.to_json()
                    }
                )
            ).to_json()))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def webhook_config_create(self, config: WebhookConfig) -> DataNode:
        data, http_response = self.post(
            PrimeTypes.WEBHOOK_CONFIGS,
            data=ujson.dumps(RootDataNode(
                data=DataNode(
                    type="webhook-configs",
                    attributes={
                        **config.to_json()
                    }
                )
            ).to_json()))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def get_contingent_holds(self, custody_account_id: str) -> RootListDataNode:
        data, http_response = self.get(PrimeTypes.CONTINGENT_HOLDS,
                                       params={
                                           'account.id': custody_account_id
                                       })
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return RootListDataNode.from_json(data.to_dict())

    @require_connection
    def get_account_totals(self, custody_account_id: str) -> RootListDataNode:
        data, http_response = self.get(PrimeTypes.ACCOUNT_CASH_TOTALS,
                                       params={
                                           'account.id': custody_account_id
                                       })
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return RootListDataNode.from_json(data.to_dict())

    @require_connection
    def sandbox_custody_account_kyc_document_uploaded_verified(self, kyc_document_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.KYC_DOCUMENT_CHECKS, f'{kyc_document_id}', 'sandbox', 'verify'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_custody_account_kyc_document_uploaded_fail(self, kyc_document_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.KYC_DOCUMENT_CHECKS, f'{kyc_document_id}', 'sandbox', 'fail'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_custody_account_cip_check_approve(self, cip_check_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.CIP_CHECKS, f'{cip_check_id}', 'sandbox', 'approve'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_custody_account_cip_check_deny(self, cip_check_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.CIP_CHECKS, f'{cip_check_id}', 'sandbox', 'deny'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_fund_transfer_clear(self, fund_transfer_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.FUND_TRANSFER, f'{fund_transfer_id}', 'sandbox', 'clear'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_fund_transfer_settle(self, fund_transfer_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.FUND_TRANSFER, f'{fund_transfer_id}', 'sandbox', 'settle'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_fund_transfer_reverse(self, fund_transfer_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.FUND_TRANSFER, f'{fund_transfer_id}', 'sandbox', 'reverse'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_contingent_holds_clear(self, contingent_hold_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.CONTINGENT_HOLDS, contingent_hold_id, self._environment, 'clear'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def sandbox_authorize_disbursment(self, disbursment_auth_id: str) -> DataNode:
        data, http_response = self.post(
            os.path.join(PrimeTypes.DISBURSEMENTS_AUTH, disbursment_auth_id, self._environment, 'verify-owner'))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

    @require_connection
    def disbursment_authorization_get(self, custody_account_id: str) -> RootListDataNode:
        data, http_response = self.get(PrimeTypes.DISBURSEMENTS_AUTH,
                                       params={
                                           'account.id': custody_account_id
                                       })
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return RootListDataNode.from_json(data.to_dict())

    @require_connection
    def custody_account_get(self, custody_account_id: str) -> DataNode:
        data, http_response = self.get(os.path.join(PrimeTypes.CUSTODY_ACCOUNT, custody_account_id))
        if 'errors' in data.to_dict():
            raise PrimeTrustError(str(data), data)
        return DataNode.from_json(data.data.to_dict())

