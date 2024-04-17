from flask import Blueprint, request
from stores import BaseStore

from flask import request, jsonify

blueprint = Blueprint("webhook", __name__)

from models.webhook import Webhook


@blueprint.route("/<oid>/<token>/", methods=["POST"])
def main(oid, token):

    # quickly verify the access using oid and token
    # if not valid, return 401
    wh_bucket = Webhook.query.filter_by(oid=oid, token=token).first()
    if wh_bucket is None:
        return jsonify({"message": "Invalid Webhook"}), 404

    # Get data from request
    data = request.get_json()  # Assumes JSON payload

    # Check if data is present
    if not data:
        return jsonify({"message": "Empty Data or improper data"}), 400

    # Get store instance
    store = BaseStore.get_provider()
    store.webhook = wh_bucket

    # Store data
    status, response = store.store(data)
    if not status:
        return jsonify({"message": "Error storing data"}), 500

    return jsonify({"oid": response.get("oid"), "ts": response.get("ts"), "message": "Data stored successfully"}), 200


@blueprint.route("/register/", methods=["POST"])
def register():
    # Get email and target_bucket from request
    data = request.get_json()
    email = data.get("email").strip()

    def is_valid_email(email):
        if email is None or email == "" or len(email) > 100:
            return False
        if "@" not in email:
            return False
        return True

    # Validate email format (basic check)
    # TODO Email validation
    if not is_valid_email(email):
        return jsonify({"message": "Invalid email format"}), 400

    hook_bucket, message = Webhook.create(email=email)
    if hook_bucket is None:
        return jsonify({"message": "Webhook registration failed for the email", "error": message}), 400

    hook_url = f"http://localhost:5000/webhook/{hook_bucket.oid}/{hook_bucket.token}"

    # Set cache for target_bucket with unique_url
    #     cache.set(target_bucket, unique_url)

    # Return success response with unique URL
    return jsonify(
        {
            "hook_url": hook_url,
            "hook_bucket": hook_bucket.oid,
            "hook_token": hook_bucket.token,
            "hook_email": email,
            "message": "Webhook registered successfully!",
        }
    )
