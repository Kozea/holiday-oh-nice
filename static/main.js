(function() {
  var $current_opt, gg_cal, local_source, shift, slot_id, slot_label;

  shift = false;

  gg_cal = 'https://www.google.com/calendar/ical/fr.french' + '%23holiday%40group.v.calendar.google.com/public/basic.ics';

  slot_id = null;

  slot_label = null;

  $current_opt = null;

  local_source = {
    color: '#3a87ad'
  };

  $(document).bind('keyup keydown', function(e) {
    return shift = e.shiftKey;
  });

  $(document).ready(function() {
    var add, calendar, get_remaining, get_slot, set_remaining, set_slot;
    window._cal = calendar = $(".calendar").fullCalendar({
      header: {
        left: "",
        right: "prev,next today",
        center: "title"
      },
      firstDay: 1,
      selectable: true,
      selectHelper: true,
      select: function(start, end, allDay) {
        var day, results;
        if ($('.delete-btn').hasClass('fc-state-down')) {
          calendar.fullCalendar("unselect");
          return;
        }
        day = start.clone();
        results = [];
        while (day.diff(end, 'days') < 0) {
          add(day);
          results.push(day.add(1, 'days'));
        }
        return results;
      },
      eventClick: function(event, jsEvent, view) {
        var ref, remaining;
        window.e = event;
        remaining = get_remaining();
        if ($('.delete-btn').hasClass('fc-state-down')) {
          if (event.className.length && ((ref = event.className[0]) === 'full' || ref === 'am' || ref === 'pm')) {
            calendar.fullCalendar('removeEvents', function(e) {
              return e === event;
            });
            if (event.className[0] === 'full') {
              set_remaining(remaining + 1);
            } else {
              set_remaining(remaining + .5);
            }
          }
          return;
        }
        if (event.className.indexOf('full') > -1) {
          event.className = ['am'];
          event.color = '#88bcd6';
          event.title += ' (Matin)';
          set_remaining(remaining + .5);
        } else if (event.className.indexOf('am') > -1) {
          event.className = ['pm'];
          event.color = '#6bb3d6';
          event.title = event.title.replace('Matin', 'Après-midi');
        } else if (event.className.indexOf('pm') > -1 && remaining > .5) {
          set_remaining(remaining - .5);
          event.className = ['full'];
          event.color = '#3a87ad';
          event.title = event.title.replace(' (Après-midi)', '');
        } else if (event.className.indexOf('pm') > -1) {
          event.className = ['am'];
          event.color = '#88bcd6';
          event.title = event.title.replace('Après-midi', 'Matin');
        }
        return calendar.fullCalendar('updateEvent', event);
      },
      editable: true,
      eventSources: [
        {
          url: gg_cal,
          color: '#ff724d',
          className: 'holiday',
          editable: false
        }, {
          events: function(start, end, tz, callback) {
            return $.ajax({
              url: "/events/from/" + (start.utc().format().replace('+00:00', 'Z')) + "/to/" + (end.utc().format().replace('+00:00', 'Z')),
              dataType: 'json',
              success: function(json) {
                return callback(json.events);
              }
            });
          },
          color: '#ffce4d',
          className: 'server',
          editable: false
        }
      ]
    });
    add = function(day_) {
      var cls, label, realEvent, ref, remaining;
      realEvent = day_.diff(moment(), 'days') > -1 && ((ref = day_.day()) !== 0 && ref !== 6) && calendar.fullCalendar('clientEvents', (function(e) {
        return day_.diff(moment(e.start), 'days', true) === 0;
      })).length === 0;
      if (!realEvent && !shift) {
        calendar.fullCalendar("unselect");
        return;
      }
      if ($current_opt === null) {
        return;
      }
      remaining = get_remaining() - 1;
      if (remaining < -.5) {
        return;
      }
      cls = ['full'];
      label = slot_label;
      if (remaining === -.5) {
        label += ' (Matin)';
        cls = ['am'];
        remaining = 0;
      }
      set_remaining(remaining);
      calendar.fullCalendar("renderEvent", {
        title: label,
        start: new Date(day_.toDate()),
        allDay: true,
        className: cls
      }, true);
      return calendar.fullCalendar("unselect");
    };
    $('.calendar .fc-left').append($('<button>', {
      type: "button",
      "class": 'save-btn fc-button fc-state-default fc-corner-left fc-corner-right',
      text: 'Sauvegarder'
    }).hover((function() {
      return $(this).addClass('fc-state-hover');
    }), (function() {
      return $(this).removeClass('fc-state-hover fc-state-down');
    })).mousedown((function() {
      return $(this).addClass('fc-state-down');
    })).mouseup((function() {
      return $(this).removeClass('fc-state-down');
    })).click(function() {
      var data, event, events, i, j, len, len1, type, types;
      events = calendar.fullCalendar('clientEvents', (function(e) {
        var ref;
        return (ref = e.className[0]) === 'full' || ref === 'am' || ref === 'pm';
      }));
      data = [];
      for (i = 0, len = events.length; i < len; i++) {
        event = events[i];
        if (event.className[0] === 'full') {
          types = ['am', 'pm'];
        } else {
          types = [event.className[0]];
        }
        for (j = 0, len1 = types.length; j < len1; j++) {
          type = types[j];
          data.push({
            day: event.start.utc().format().replace('+00:00', 'Z'),
            type: type,
            slot: get_slot(event.title.split('(')[0].trim())
          });
        }
      }
      if (data.length) {
        $.ajax({
          url: '/events/save',
          data: {
            events: JSON.stringify(data)
          },
          type: 'POST',
          success: function() {
            return location.reload();
          }
        });
      }
      return false;
    }), $('<button>', {
      type: "button",
      "class": 'delete-btn fc-button fc-state-default fc-corner-left fc-corner-right',
      text: 'Mode suppression'
    }).hover((function() {
      return $(this).addClass('fc-state-hover');
    }), (function() {
      return $(this).removeClass('fc-state-hover');
    })).mousedown((function() {
      return $(this).toggleClass('fc-state-down');
    })));
    get_remaining = function() {
      return parseFloat($current_opt.attr('data-remaining'));
    };
    set_remaining = function(remaining) {
      $current_opt.attr('data-remaining', remaining);
      return $('.remaining').text(remaining);
    };
    get_slot = function(label) {
      var i, len, opt, ref;
      ref = $('.slot option');
      for (i = 0, len = ref.length; i < len; i++) {
        opt = ref[i];
        if ($(opt).text() === label) {
          return $(opt).attr('value');
        }
      }
    };
    set_slot = function() {
      slot_id = $(this).val();
      $current_opt = $(this).find("option[value=" + slot_id + "]");
      slot_label = $current_opt.text();
      return $('.remaining').text($current_opt.attr('data-remaining'));
    };
    set_slot.call($('.slot'));
    return $('.slot').change(set_slot);
  });

}).call(this);
