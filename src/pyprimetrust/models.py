from jsonobject import *


def reconstruct(root: JsonObject.__class__, data):
    if root is None:
        return data

    for key, type in root._properties_by_attr.items():
        if isinstance(type, (ListProperty,)) and key in data:
            data[key] = [reconstruct(getattr(type.item_wrapper,'item_type', None), item) for item in data[key]]
        elif isinstance(type, (DictProperty,)) and key in data:
            data[key] = {in_key: reconstruct(getattr(type.item_wrapper,'item_type', None), value) for in_key, value in data[key].items()}
        elif isinstance(type, (ObjectProperty,)) and key in data:
            data[key] = reconstruct(type.item_type, data[key])

    if 'self' in data:
        data['_self'] = data['self']
        del data['self']
    return root(**data)


class Links(JsonObject):
    _self = StringProperty(name='self')
    first = StringProperty(exclude_if_none=True)
    related = StringProperty(exclude_if_none=True)


class Relationship(JsonObject):
    links = ObjectProperty(Links)


class DataNode(JsonObject):
    type = StringProperty()
    id = StringProperty(exclude_if_none=True)
    attributes = DictProperty()
    links = ObjectProperty(Links, exclude_if_none=True)
    relationships = DictProperty(Relationship, exclude_if_none=True)


class Meta(JsonObject):
    page_count = IntegerProperty(name='page-count')
    resource_count = IntegerProperty(name='resource-count')


class RootListDataNode(JsonObject):
    data = ListProperty(DataNode)
    links = ObjectProperty(Links)
    meta = ObjectProperty(Meta)


class RootDataNode(JsonObject):
    data = ObjectProperty(DataNode)


class PhoneNumber(JsonObject):
    country = StringProperty()
    number = StringProperty()
    sms = BooleanProperty()


class Address(JsonObject):
    street_1 = StringProperty(name='street-1')
    street_2 = StringProperty(name='street-2')
    postal_code = StringProperty(name='postal-code')
    city = StringProperty()
    region = StringProperty()
    country = StringProperty()


class Contact(JsonObject):
    contact_type = StringProperty(name='contact-type', choices=['natural_person', 'company'], default='natural_person')
    name = StringProperty()
    email = StringProperty()
    date_of_birth = DateProperty(name='date-of-birth', exclude_if_none=True)
    sex = StringProperty(choices=['male', 'female'], exclude_if_none=True)
    tax_id_number = StringProperty(name='tax-id-number')
    tax_country = StringProperty(name='tax-country')
    label = StringProperty(exclude_if_none=True)
    primary_phone_number = ObjectProperty(PhoneNumber, name='primary-phone-number')
    primary_address = ObjectProperty(Address, name='primary-address')
    region_of_formation = StringProperty(name='region-of-formation', exclude_if_none=True)
    related_contacts = ListProperty(ObjectProperty, name='related-contacts', exclude_if_none=True)


Contact.related_contacts.item_wrapper._item_type = Contact


class FundTransferMethod(JsonObject):
    bank_account_name = StringProperty(name='bank-account-name')
    routing_number = StringProperty(name='routing-number', exclude_if_none=True)
    ip_address = StringProperty(name='ip-address')
    bank_account_type = StringProperty(name='bank-account-type', exclude_if_none=True)
    bank_account_number = StringProperty(name='bank-account-number', exclude_if_none=True)
    ach_check_type = StringProperty(name='ach-check-type')
    funds_transfer_type = StringProperty(name='funds-transfer-type')
    plaid_public_token = StringProperty(name='plaid-public-token', exclude_if_none=True)
    plaid_account_id = StringProperty(name='plaid-account-id', exclude_if_none=True)


class AccountQuestionnaire(JsonObject):
    nature_of_business_of_the_company = StringProperty(name='nature-of-business-of-the-company')
    purpose_of_account = StringProperty(name='purpose-of-account')
    source_of_assets_and_income = StringProperty(name='source-of-assets-and-income')
    intended_use_of_account = StringProperty(name='intended-use-of-account')
    anticipated_monthly_cash_volume = StringProperty(name='anticipated-monthly-cash-volume')
    anticipated_monthly_transactions_incoming = StringProperty(name='anticipated-monthly-transactions-incoming')
    anticipated_monthly_transactions_outgoing = StringProperty(name='anticipated-monthly-transactions-outgoing')
    anticipated_types_of_assets = StringProperty(name='anticipated-types-of-assets')
    anticipated_trading_patterns = StringProperty(name='anticipated-trading-patterns')
    associations_with_other_accounts = StringProperty(name='associations-with-other-accounts')
