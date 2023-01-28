# from django_filters import rest_framework as filters

# class ReportSearchFilter(filters.FilterSet):
#     districts = filters.ChoiceFilter(choices=DISTRICTS, required=False)
#     keywords = filters.CharFilter(
#         label="Keywords",
#         widget=forms.TextInput(attrs={"placeholder": "mole on left hand"}),
#         required=False,
#         max_length=100,
#         validators=[
#             RegexValidator("^((?!AND).)*$", message="Cannot contain 'AND' "),
#             RegexValidator("^((?!NOT).)*$", message="Cannot contain 'NOT' "),
#         ],
#     )
#     full_text_search_type = filters.IntegerFilter(
#         label="Keyword Search Type",
#         widget=forms.RadioSelect(choices=FULL_TEXT_SEARCH_TYPE),
#     )
#     missing_or_found = filters.CharFilter(
#         label="Missing or Found",
#         required=False,
#         widget=forms.RadioSelect(choices=[("All", "All")] + MISSING_OR_FOUND),
#     )
#     gender = filters.CharFilter(
#         label="Gender",
#         required=False,
#         widget=forms.RadioSelect(choices=[("All", "All")] + GENDER[:-1]),
#     )
#     min_date = filters.DateFilter(required=False)
#     max_date = filters.DateFilter(required=False)
#     ps_list = filters.CharFilter(required=False, widget=forms.HiddenInput())
#     latitude = filters.CharFilter(required=False, max_length=20)
#     longitude = filters.CharFilter(required=False, max_length=20)
#     # location = filters.SpatialFilter(map_attrs=default_map_attrs
