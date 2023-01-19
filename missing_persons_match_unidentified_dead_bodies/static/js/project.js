/* Project specific Javascript goes here. */
// This file is automatically compiled by Webpack, along with any other files
// present in this directory. You're encouraged to place your actual application logic in
// a relevant structure within app/javascript and only use these pack files to reference
// that code so it'll be compiled.
var availablePSs
$(document).ready(function() {
    var elementExists = document.getElementById("ps_list");
    if (elementExists) {
        var ps = "";
        var pscode = [];
        const availablePSsArray = JSON.parse(document.getElementById('ps_list').textContent);
        var availablePSs = availablePSsArray.map(x => " ".concat(x[1]));
        var elementExists2 = document.getElementById("police_station_id");
        $("#police_station_id").empty();
        // console.log(elementExists2);

        if (elementExists2) {
            // console.log("ps selector is here");
            var options_for_ps = '<option value="' + "" + '">' + "" + '</option>';
            for (var i = 0; i < availablePSs.length; i++) {
                options_for_ps += '<option value="' + availablePSsArray[i][0] + '">' + availablePSsArray[i][1] + '</option>';

            }
            $("#police_station_id").append(options_for_ps);
            // console.log(elementExists2);
        }

        function split(val) {
            return val.split(/, \s*/);
        }

        function extractLast(term) {
            return split(term).pop();
        }

        (function($) {
            $.widget("custom.combobox", {
                _create: function() {
                    this.wrapper = $("<span>")
                    .addClass("custom-combobox")
                    .insertAfter(this.element);

                    this.element.hide();
                    this._createAutocomplete();
                    // this._createShowAllButton();
                },

                _createAutocomplete: function() {
                    var selected = this.element.children(":selected"),
                    value = selected.val() ? selected.text() : "";

                    this.input = $("<input>")
                    .appendTo(this.wrapper)
                    .val(value)
                    .attr("title", "")
                    .addClass("custom-combobox-input ui-widget ui-widget-content ui-state-default ui-corner-left form-control input-lg")
                    .autocomplete({
                        delay: 0,
                        minLength: 0,
                        source: $.proxy(this, "_source")
                    })
                    .tooltip({
                        tooltipClass: "ui-state-highlight"
                    });

                    this._on(this.input, {
                        autocompleteselect: function(event, ui) {
                            ui.item.option.selected = true;
                            this._trigger("select", event, {
                                item: ui.item.option
                            });

                            if ($("#psquery").length > 0) {
                                pscode.push(ui.item.option.value);
                                ps = ps + ui.item.option.text + "</br>";

                                if ($("#id_ps_list").length > 0) {
                                    document.getElementById("id_ps_list").value = pscode;
                                } else if ($("#report_search_police_stations").length > 0) {
                                    document.getElementById("report_search_police_stations").value = pscode;
                                } else {
                                    alert($("#id_ps_list").length);
                                    document.getElementById("criminal_ps_op").value = pscode;
                                }
                                document.getElementById("psquery").innerHTML = ps;
                                return false;
                            }

                        },

                        autocompletechange: "_removeIfInvalid"
                    });
                },

                _createShowAllButton: function() {
                    var input = this.input,
                    wasOpen = false;

                    $("<a>")
                    .attr("tabIndex", -1)
                    .attr("title", "Show All Items")
                    .tooltip()
                    .appendTo(this.wrapper)
                    .button({
                        icons: {
                            primary: "ui-icon-triangle-1-s"
                        },
                        text: false
                    })
                    .removeClass("ui-corner-all")
                    .addClass("custom-combobox-toggle ui-corner-right")
                    .mousedown(function() {
                        wasOpen = input.autocomplete("widget").is(":visible");
                    })
                    .click(function() {
                        input.focus();

                            // Close if already visible
                        if (wasOpen) {
                            return;
                        }

                            // Pass empty string as value to search for, displaying all results
                        input.autocomplete("search", "");
                    });
                },

                _source: function(request, response) {
                    var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
                    response(this.element.children("option").map(function() {
                        var text = $(this).text();
                        if (this.value && (!request.term || matcher.test(text)))
                            return {
                                label: text,
                                value: text,
                                option: this
                            };
                        }));
                },

                _removeIfInvalid: function(event, ui) {

                    // Selected an item, nothing to do
                    if (ui.item) {
                        return;
                    }

                    // Search for a match (case-insensitive)
                    var value = this.input.val(),
                    valueLowerCase = value.toLowerCase(),
                    valid = false;
                    this.element.children("option").each(function() {
                        if ($(this).text().toLowerCase() === valueLowerCase) {
                            this.selected = valid = true;
                            return false;
                        }
                    });

                    // Found a match, nothing to do
                    if (valid) {
                        return;
                    }

                    // Remove invalid value
                    this.input
                    .val("")
                    .attr("title", value + " didn't match any item")
                    .tooltip("open");
                    this.element.val("");
                    this._delay(function() {
                        this.input.tooltip("close").attr("title", "");
                    }, 2500);
                    this.input.autocomplete("instance").term = "";
                },

                _destroy: function() {
                    this.wrapper.remove();
                    this.element.show();
                }

            });


})(jQuery);

$(function() {
    $("#police_station_id").combobox();

});



$(function() {
    $('#id_advanced_search_report').change(function() {
        $('.basic-search-fields').toggle(!this.checked);
        $('.advanced-search-fields').toggle(this.checked);
            }).change(); //ensure visible state matches initially
});



        // Let's check if the browser supports notifications
if (!("Notification" in window)) {

}

        // Let's check whether notification permissions have already been granted
else if (Notification.permission === "granted") {
            // If it's okay let's create a notification

}

        // Otherwise, we need to ask the user for permission
else if (Notification.permission !== 'denied') {
    Notification.requestPermission(function(permission) {
                // If the user accepts, let's create a notification
        if (permission === "granted") {

        }
    });
}

        // Finally, if the user has denied notifications and you
        // want to be respectful there is no need to bother them any more.
};
$(document).on('focus', "input[id$='date']", function() {
    selected_id = "#" + $(this).first().attr("id");

    $(selected_id).datepicker({
        dateFormat: 'yy-mm-dd'
    });
    $(selected_id).change(function() {
        $(selected_id).datepicker("destroy");
    });

});

$(document).on('focus', "input[id$='police_station_with_distt']", function() {
    selected_id = "#" + $(this).first().attr("id");
    $(selected_id).autocomplete({
        source: availablePSs,
        change: function(event, ui) {
                // This block of code ensures that values are restricted to list items
            if (ui.item == null) {
                event.currentTarget.value = '';
                event.currentTarget.focus();
            }
                // This block of code ensures that values are restricted to list items
            else {
                $(selected_id).autocomplete("destroy");
            }
        }

    });


});

$(function() {

    var public_link = document.getElementById("public_link");

    $('#public_link').click(function() {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(function(position) {
            var latitude = position.coords.latitude;
            var longitude = position.coords.longitude;



            // $(form).find('#id_advanced_search_report').prop('checked', true);

            // $(form).find('#id_gender_0').prop('checked', true);

            // $(form).find('#id_missing_or_found_0').prop('checked', true);

            var today = new Date();
            var oneMonthAgo = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
            console.log("Latitude: " + latitude + ", Longitude: " + longitude);
            console.log("today: " + today.toISOString().slice(0, 10) + ", oneMonthAgo: " + oneMonthAgo.toISOString().slice(0, 10));
             $.ajax({
            url: '/ajax/public_missing/',
            data: {
                'latitude': latitude,
                'longitude': longitude,
                'min_date': oneMonthAgo.toISOString().slice(0, 10),
                'max_date': today.toISOString().slice(0, 10)
            },
            dataType: 'json',
            success: function(data) {
                console.log(data.results)


                                // nodes = result["nodes"];

                                // var edges = result["relationships"]


                // displaying gist on select

                            // network.on('click', function(properties) {
                            //     node = getNodeByUUID(properties.nodes[0]);


                            //     if (node[0].group == "Crime") {
                            //         $.ajax({
                            //             url: '/ajax/crimes/',
                            //             data: {
                            //                 'unique_id': properties.nodes[0]
                            //             },
                            //             dataType: 'json',
                            //             success: function(data) {
                            //                 alert('Gist: ' + data.gist);
                            //             },
                            //         });
                            //     }
                            // });
                // displaying gist on select -> end
                // navigating on hold
                        // network.on('hold', function(properties) {
                        //     node = getNodeByUUID(properties.nodes[0]);
                        //     if (node[0].group == "Crime") {
                        //         window.location.assign('/backend/crimes/' + properties.nodes[0])
                        //     } else {
                        //         window.location.assign('/graphs/criminals/' + properties.nodes[0])
                        //     }
                        // });
                //navigating on hold -> end
            }
        });

            // $(form).find('#id_min_date').value = oneMonthAgo.toISOString().slice(0, 10);
            // $(form).find('#id_max_date').value = today.toISOString().slice(0, 10);
            // $(form).find('#id_longitude').value = longitude;
            // $(form).find('#id_latitude').value = latitude;
            // $(form).find('#id_distance').value = today.toISOString().slice(0, 10);
            // $(form).find('#id_max_date').value = today.toISOString().slice(0, 10);


            // formElement.getElementById('').value = 20;

            // formElement.getElementById('id_map_or_list_0').click();

            // formElement.getElementById('submit-id-submit').click();





});
      } else {
          console.log("Geolocation is not supported by this browser.");
      }


            }); //ensure visible state matches initially






});


});
