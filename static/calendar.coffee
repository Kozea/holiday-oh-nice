shift = false

$(document).bind 'keyup keydown', (e) -> shift = e.shiftKey


$(document).ready ->
    window._cal = calendar = $(".calendar").fullCalendar(
        header:
            left: "prev,next today"
            center: "title"

        firstDay: 1
        selectable: true
        selectHelper: true
        eventColor: '#3a87ad'
        select: (start, end, allDay) ->
            start = moment(start)
            end = moment(end)
            day = moment(start)
            while day.diff(end, 'days') < 1
                add(day)
                day.add('days', 1)

        editable: true
        eventSources: [
                url: 'http://www.google.com/calendar/feeds/french__fr@holiday.calendar.google.com/public/basic'
                color: '#ff724d'
                className: 'holiday'
            ,
                url: location.href
                color: '#ffce4d'
                className: 'server'
        ]
    )

    add = (day_) ->
        realEvent = day_.day() not in [0, 6] and calendar.fullCalendar('clientEvents', (
            (e) -> day_.diff(moment(e.start), 'days', true) == 0)
        ).length == 0

        if not realEvent and not shift
            calendar.fullCalendar "unselect"
            return

        calendar.fullCalendar "renderEvent",
                title: "Congé"
                start: new Date(day_.toDate())
                allDay: true
                className: 'new'
                color: '#3a87ad'
            , true
        calendar.fullCalendar "unselect"
