"""PurplShip Australia post rate mapper module."""

from typing import List, Tuple
from pyaups.shipping_price_request import ShippingPriceRequest, Shipment, From, To, Item
from purplship.carriers.aups.error import parse_error_response
from purplship.carriers.aups.units import PackagingType
from purplship.core.utils import jsonify, to_dict, Serializable, decimal
from purplship.core.models import Message, ChargeDetails, RateRequest, RateDetails
from purplship.core.units import Currency, Country
from purplship.carriers.aups.utils import Settings
from purplship.core.errors import OriginNotServicedError
from pyaups.shipping_price_response import (
    ShippingPriceResponse,
    Shipment as ResponseShipment,
    ShipmentSummary,
)


def parse_shipping_price_response(
    response: dict, settings: Settings
) -> Tuple[List[RateDetails], List[Message]]:
    price_response: ShippingPriceResponse = ShippingPriceResponse(**response)
    return (
        [_extract_quote(rate, settings) for rate in price_response.shipments],
        parse_error_response({"errors": response.get("errors", [])}, settings),
    )


def _extract_quote(rate: ResponseShipment, settings: Settings) -> RateDetails:
    summary = rate.shipment_summary or ShipmentSummary()

    surcharges = {
        "Fuel": summary.fuel_surcharge,
        "Security": summary.security_surcharge,
        "Transit Cover": summary.transit_cover,
        "Freight Charge": summary.freight_charge
    }
    extra_charges = [
        ChargeDetails(name=name, amount=decimal(amount), currency=Currency.AUD.name)
        for name, amount in surcharges.items() if amount is not None
    ]

    return RateDetails(
        carrier=settings.carrier,
        carrier_name=settings.carrier_name,
        base_charge=decimal(summary.total_cost_ex_gst),
        duties_and_taxes=decimal(summary.total_gst),
        total_charge=decimal(summary.total_cost),
        currency=Currency.AUD.name,
        discount=decimal(summary.discount),
        extra_charges=extra_charges,
    )


def shipping_price_request(payload: RateRequest) -> Serializable[ShippingPriceRequest]:
    """Create the appropriate Australia post rate request depending on the destination

    :param payload: PurplShip unified API rate request data
    :return: a domestic or international Australia post compatible request
    :raises: an OriginNotServicedError when origin country is not serviced by the carrier
    """
    if payload.shipper.country_code and payload.shipper.country_code != Country.AU.name:
        raise OriginNotServicedError(payload.shipper.country_code, "Australia post")

    packaging_type = next(
        (t.value for t in PackagingType if t.name == payload.parcel.packaging_type),
        None
    )

    request = ShippingPriceRequest(
        shipments=[
            Shipment(
                shipment_reference=payload.parcel.reference,
                sender_references=None,
                goods_descriptions=None,
                despatch_date=None,
                consolidate=None,
                email_tracking_enabled=payload.shipper.email is not None,
                from_=From(
                    name=payload.shipper.person_name,
                    type=None,
                    lines=[
                        payload.shipper.address_line1,
                        payload.shipper.address_line2,
                    ],
                    suburb=payload.shipper.suburb,
                    state=payload.shipper.state_code,
                    postcode=payload.shipper.postal_code,
                    country=payload.shipper.country_code,
                    phone=payload.shipper.phone_number,
                    email=payload.shipper.email,
                ),
                to=To(
                    name=payload.recipient.person_name,
                    business_name=payload.recipient.company_name,
                    type=None,
                    lines=[
                        payload.recipient.address_line1,
                        payload.recipient.address_line2,
                    ],
                    suburb=payload.recipient.suburb,
                    state=payload.recipient.state_code,
                    postcode=payload.recipient.postal_code,
                    country=payload.recipient.country_code,
                    phone=payload.recipient.phone_number,
                    email=payload.recipient.email,
                    delivery_instructions=None,
                ),
                dangerous_goods=None,
                movement_type=None,
                features=None,
                authorisation_number=None,
                items=[
                    Item(
                        item_reference=payload.parcel.reference,
                        product_id=payload.parcel.id,
                        item_description=payload.parcel.description,
                        length=payload.parcel.length,
                        width=payload.parcel.width,
                        height=payload.parcel.height,
                        cubic_volume=None,
                        weight=payload.parcel.weight,
                        contains_dangerous_goods=None,
                        transportable_by_air=None,
                        dangerous_goods_declaration=None,
                        authority_to_leave=False,
                        reason_for_return=None,
                        allow_partial_delivery=True,
                        packaging_type=packaging_type,
                        atl_number=None,
                        features=None,
                        tracking_details=None,
                        commercial_value=None,
                        export_declaration_number=None,
                        import_reference_number=None,
                        classification_type=None,
                        description_of_other=None,
                        international_parcel_sender_name=None,
                        non_delivery_action=None,
                        certificate_number=None,
                        licence_number=None,
                        invoice_number=None,
                        comments=None,
                        tariff_concession=None,
                        free_trade_applicable=None,
                    )
                ],
            )
        ]
    )
    return Serializable(request, _request_serializer)


def _request_serializer(request: ShippingPriceRequest) -> str:
    return jsonify(to_dict(request))
