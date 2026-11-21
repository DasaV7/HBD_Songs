import cloudinary
import cloudinary.uploader
import streamlit as st
from datetime import datetime
from datetime import timedelta

from services.sheets_service import (
    get_spreadsheet
)

from services.cloudinary_service import (
    cleanup_old_instagram_assets
)


cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

def delete_cloudinary_asset(
    public_id,
    resource_type="image"
):

    try:

        result = cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type
        )

        return result

    except Exception as e:

        print(
            f"Delete failed: {public_id}"
        )

        print(e)

        return None
        
def cleanup_old_instagram_assets(
    days_old=3
):

    spreadsheet = get_spreadsheet()

    ws = spreadsheet.worksheet(
        "InstagramAssets"
    )

    records = ws.get_all_records()

    cutoff_date = (
        datetime.now()
        - timedelta(days=days_old)
    )

    deleted_count = 0

    for idx, row in enumerate(
        records,
        start=2
    ):

        try:

            created = datetime.strptime(
                row["created_date"],
                "%Y-%m-%d %H:%M:%S"
            )

            if created > cutoff_date:
                continue

            reel_id = row.get(
                "reel_public_id",
                ""
            )

            post_id = row.get(
                "post_public_id",
                ""
            )

            if reel_id:

                delete_cloudinary_asset(
                    reel_id,
                    resource_type="video"
                )

            if post_id:

                delete_cloudinary_asset(
                    post_id,
                    resource_type="image"
                )

            ws.update_cell(
                idx,
                5,
                "Deleted"
            )

            deleted_count += 1

        except Exception as e:

            print(
                f"Cleanup failed row {idx}: {e}"
            )

    return deleted_count

try:

    deleted = cleanup_old_instagram_assets(
        days_old=3
    )

    print(
        f"Removed {deleted} old assets"
    )

except Exception as e:

    print(
        f"Cleanup error: {e}"
    )
