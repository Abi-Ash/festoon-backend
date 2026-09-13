import cloudinary
import cloudinary.uploader
from flask import current_app


def init_cloudinary(app):
    cloudinary.config(
        cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=app.config["CLOUDINARY_API_KEY"],
        api_secret=app.config["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_product_image(file_storage):
    """
    Uploads a werkzeug FileStorage object to Cloudinary and returns the
    secure HTTPS URL. Raises Exception on failure (caller should catch it).
    """
    if not current_app.config["CLOUDINARY_CLOUD_NAME"]:
        raise RuntimeError(
            "Cloudinary is not configured. Set CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET in your .env file."
        )
    result = cloudinary.uploader.upload(
        file_storage,
        folder="festoon/products",
        resource_type="image",
    )
    return result.get("secure_url")


def upload_product_images(file_storage_list):
    """
    Uploads several files (e.g. request.files.getlist("images")) and returns
    their secure URLs in the same order. Stops and raises on the first
    failure rather than partially uploading - callers should treat this as
    all-or-nothing so a product never ends up with a broken gallery entry.
    """
    return [upload_product_image(f) for f in file_storage_list if f and f.filename]
