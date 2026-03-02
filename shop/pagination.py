from rest_framework.pagination import PageNumberPagination


# Custom pagination class
# Extends DRF PageNumberPagination with configurable page size
class DefaultPagination(PageNumberPagination):

    # Default number of items per page
    page_size = 20

    # Allow client to override page size using ?page_size=
    page_size_query_param = "page_size"

    # Maximum allowed page size to prevent abuse
    max_page_size = 200