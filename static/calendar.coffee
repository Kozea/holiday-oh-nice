shift = false
slot_id = null
slot_label = null
$current_opt = null
local_source = {
    color: '#3a87ad'
}

$(document).bind 'keyup keydown', (e) -> shift = e.shiftKey


$(document).ready ->
    window._cal = calendar = $(".calendar").fullCalendar(
        header:
            left: ""
            right: "prev,next today"
            center: "title"

        firstDay: 1
        selectable: true
        selectHelper: true
        select: (start, end, allDay) ->
            if $('.delete-btn').hasClass('fc-state-down')
                calendar.fullCalendar "unselect"
                return
            start = moment(start)
            end = moment(end)
            day = moment(start)
            while day.diff(end, 'days') < 1
                add(day)
                day.add('days', 1)

        eventClick: (event, jsEvent, view) ->
            window.e = event
            remaining = get_remaining()

            if $('.delete-btn').hasClass('fc-state-down')
                if event.className.length and event.className[0] in ['full', 'am', 'pm']
                    calendar.fullCalendar('removeEvents', (e) -> e == event)
                    if event.className[0] == 'full'
                        set_remaining(remaining + 1)
                    else
                        set_remaining(remaining + .5)
                return

            if event.className.indexOf('full') > -1
                event.className = ['am']
                event.color = '#88bcd6'
                event.title += ' (Matin)'
                set_remaining(remaining + .5)
            else if event.className.indexOf('am') > -1
                event.className = ['pm']
                event.color = '#6bb3d6'
                event.title = event.title.replace('Matin', 'Après-midi')
            else if event.className.indexOf('pm') > -1 and remaining > .5
                set_remaining(remaining - .5)
                event.className = ['full']
                event.color = '#3a87ad'
                event.title = event.title.replace(' (Après-midi)', '')
            else if event.className.indexOf('pm') > -1
                event.className = ['am']
                event.color = '#88bcd6'
                event.title = event.title.replace('Après-midi', 'Matin')
            calendar.fullCalendar('updateEvent', event)

        editable: true
        eventSources: [
                url: 'http://www.google.com/calendar/feeds/french__fr@holiday.calendar.google.com/public/basic'
                color: '#ff724d'
                className: 'holiday'
                editable: false
            ,
                events: (start, end, callback) ->
                    $.ajax
                        url: '/events/from/' + $.fullCalendar.formatDate(start, 'u') + '/to/' + $.fullCalendar.formatDate(end, 'u')
                        dataType: 'json'
                        success: (json) ->
                            # for event in json.events
                                # event.color =
                            callback(json.events)
                color: '#ffce4d'
                className: 'server'
                editable: false
        ]
    )

    add = (day_) ->
        realEvent = day_.diff(moment(), 'days') > -1 and day_.day() not in [0, 6] and calendar.fullCalendar('clientEvents', (
            (e) -> day_.diff(moment(e.start), 'days', true) == 0)
        ).length == 0
        if not realEvent and not shift
            calendar.fullCalendar "unselect"
            return
        if $current_opt == null
            return
        remaining = get_remaining() - 1
        if remaining < -.5
            return

        cls = ['full']
        label = slot_label
        if remaining == -.5
            label += ' (Matin)'
            cls = ['am']
            remaining = 0
        set_remaining(remaining)
        calendar.fullCalendar "renderEvent",
                title: label
                start: new Date(day_.toDate())
                allDay: true
                className: cls
            , true
        calendar.fullCalendar "unselect"

    $('.calendar .fc-header-left').append(
        $('<span>', class: 'save-btn fc-button fc-state-default fc-corner-left fc-corner-right')
            .text('Save')
            .hover(
                (-> $(@).addClass('fc-state-hover')),
                (-> $(@).removeClass('fc-state-hover fc-state-down')))
            .mousedown((-> $(@).addClass('fc-state-down')))
            .mouseup((-> $(@).removeClass('fc-state-down')))
            .click(->
                events = calendar.fullCalendar('clientEvents', ((e) -> e.className[0] in ['full', 'am', 'pm']))
                data = []
                for event in events
                    if event.className[0] == 'full'
                        types = ['am', 'pm']
                    else
                        types = [event.className[0]]
                    for type in types
                        data.push(
                            day: $.fullCalendar.formatDate(event.start, 'u')
                            type: type
                            slot: get_slot(event.title.split('(')[0].trim())
                        )

                if data.length
                    $.ajax(
                        url: '/events/save'
                        data: events: JSON.stringify(data)
                        type: 'POST'
                        success: ->
                            location.reload())

                false
            ),
        $('<span>', class: 'delete-btn fc-button fc-state-default fc-corner-left fc-corner-right')
            .text('Delete')
            .hover(
                (-> $(@).addClass('fc-state-hover')),
                (-> $(@).removeClass('fc-state-hover')))
            .mousedown((-> $(@).toggleClass('fc-state-down')))
    )

    get_remaining = -> parseFloat($current_opt.attr('data-remaining'))
    set_remaining = (remaining) ->
        $current_opt.attr('data-remaining', remaining)
        $('.remaining').text(remaining)

    get_slot = (label) ->
        for opt in $('.slot option')
            if $(opt).text() == label
                return $(opt).attr('value')

    set_slot = ->
        slot_id = $(@).val()
        $current_opt = $(@).find("option[value=#{slot_id}]")
        slot_label = $current_opt.text()
        $('.remaining').text($current_opt.attr('data-remaining'))

    set_slot.call($('.slot'))
    $('.slot').change(set_slot)
