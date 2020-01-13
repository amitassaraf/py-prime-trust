from enum import Enum
from typing import Tuple

from box import Box
from requests import Session, Response
from urlparse import urljoin

from .consts import BASE_API_URL, PRODUCTION_ENV, SANDBOX_ENV
from .models import *
from .utils import require_connection


class PrimeURLs(Enum):
    JWT_AUTH = '/auth/jwts'
    CUSTODY_AGREEMENT_PREVIEW = '/agreement-previews'
    CUSTODY_ACCOUNT = '/v2/accounts'
    CONTACTS = '/v2/contacts'
    FUND_TRANSFER_METHODS = '/v2/funds-transfer-methods'


class PrimeClient(Session):
    def __init__(self, root_user_email: str, root_user_password: str, debug: bool = False):
        super(PrimeClient, self).__init__()
        self._environment = SANDBOX_ENV if debug else PRODUCTION_ENV
        self._base_url = BASE_API_URL.format(self._environment)
        self._root_user_email = root_user_email
        self._root_user_password = root_user_password
        self._auth_token = None

    def request(self, method, url, *args, **kwargs) -> Tuple[Box, Response]:
        url = urljoin(self._base_url, url)
        response = super(PrimeClient, self).request(method, url, *args, **kwargs)
        return Box(response.json()), response

    def connect(self) -> bool:
        data, http_response = self.post(PrimeURLs.JWT_AUTH, auth=(self._root_user_email, self._root_user_password))
        self._auth_token = data.token
        self.headers.update('Authorization', f'Bearer {self._auth_token}')
        return True

    @require_connection
    def custody_account_agreement_preview(self, contact: Contact):
        data, http_response = self.post(PrimeURLs.CUSTODY_AGREEMENT_PREVIEW,
                                        data=RootDataNode(
                                            data=DataNode(
                                                type="account",
                                                attributes={
                                                    "account-type": "custodial",
                                                    "name": f'{contact.name}\'s Account',
                                                    "authorized-signature": f'{contact.name}',
                                                    "owner": contact.to_json()
                                                }
                                            )
                                        ).to_json())
        return DataNode(**data.data.to_dict())

    @require_connection
    def create_custody_account(self, contact: Contact):
        data, http_response = self.post(PrimeURLs.CUSTODY_ACCOUNT,
                                        data=RootDataNode(
                                            data=DataNode(
                                                type="account",
                                                attributes={
                                                    "account-type": "custodial",
                                                    "name": f'{contact.name}\'s Account',
                                                    "authorized-signature": f'{contact.name}',
                                                    "owner": contact.to_json()
                                                }
                                            )
                                        ).to_json())
        return DataNode(**data.data.to_dict())

    @require_connection
    def create_entity_custody_account(self, contact: Contact):
        data, http_response = self.post(PrimeURLs.CUSTODY_ACCOUNT,
                                        data=RootDataNode(
                                            data=DataNode(
                                                type="account",
                                                attributes={
                                                    "account-type": "custodial",
                                                    "name": f'{contact.name}\'s Account',
                                                    "authorized-signature": f'{contact.related_contacts[0].name}',
                                                    "owner": contact.to_json()
                                                }
                                            )
                                        ).to_json())
        return DataNode(**data.data.to_dict())

    @require_connection
    def activate_custody_account(self, custody_account_id):
        data, http_response = self.post(
            urljoin(PrimeURLs.CUSTODY_ACCOUNT, f'/{custody_account_id}', f'/{self._environment}', f'/open'))
        return data.data

    @require_connection
    def start_custody_kyc_process(self, custody_account_id, contact: Contact):
        data, http_response = self.post(PrimeURLs.CONTACTS,
                                        data=RootDataNode(
                                            data=DataNode(
                                                type="contacts",
                                                attributes={
                                                    "account-id": custody_account_id,
                                                    **contact.to_json()
                                                }
                                            )
                                        ).to_json())
        return DataNode(**data.data.to_dict())

    @require_connection
    def get_custody_kyc_status(self, contact_id):
        data, http_response = self.get(PrimeURLs.CONTACTS,
                                       params={
                                           'filter[contact.id eq]': contact_id,
                                           'include': 'cip-checks,aml-checks,kyc-document-checks'
                                       })
        return RootListDataNode(**data.to_dict())

    @require_connection
    def add_fund_transfer_method(self, contact_id, transfer_method: FundTransferMethod):
        data, http_response = self.post(PrimeURLs.FUND_TRANSFER_METHODS,
                                        data=RootDataNode(
                                            data=DataNode(
                                                type="funds-transfer-methods",
                                                attributes={
                                                    "contact-id": contact_id,
                                                    **transfer_method.to_json()
                                                }
                                            )
                                        ).to_json())
        return DataNode(**data.data.to_dict())
