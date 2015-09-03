import pytest
from mock import patch, Mock, call

from nefertari import events


class TestEvents(object):
    def test_request_event_init(self):
        obj = events.RequestEvent(
            view=1, model=2, fields=3, field=4, instance=5)
        assert obj.view == 1
        assert obj.model == 2
        assert obj.fields == 3
        assert obj.field == 4
        assert obj.instance == 5

    def test_set_field_value_field_name_provided(self):
        view = Mock(_json_params={})
        event = events.RequestEvent(
            view=view, model=None, field=None)
        event.set_field_value(2, 'foo')
        assert view._json_params == {'foo': 2}

    def test_set_field_value_no_field_name(self):
        from nefertari.utils import FieldData
        field = FieldData(name='foo', new_value=1)
        view = Mock(_json_params={})
        event = events.RequestEvent(
            view=view, model=None, field=field)
        event.set_field_value(2)
        assert view._json_params == {'foo': 2}

    def test_set_field_value_no_field_name_no_field(self):
        view = Mock(_json_params={})
        event = events.RequestEvent(
            view=view, model=None, field=None)
        with pytest.raises(KeyError) as ex:
            event.set_field_value(2)
        assert 'Field name is not specified' in str(ex.value)

    @patch.object(events, 'before_index')
    @patch.object(events, 'after_index')
    @patch('nefertari.utils.FieldData.from_dict')
    def test_trigger_events(self, mock_from, mock_after, mock_before):
        mock_from.return_value = {'foo': 1}
        ctx = Mock(pk_field=2)
        view = Mock(
            Model=1,
            request=Mock(action='index'),
            _json_params={'bar': 1},
            context=ctx)

        with events.trigger_events(view):
            pass

        mock_after.assert_called_once_with(
            fields={'foo': 1}, model=1, instance=ctx, view=view)
        mock_before.assert_called_once_with(
            fields={'foo': 1}, model=1, instance=ctx, view=view)
        view.request.registry.notify.assert_has_calls([
            call(mock_before()),
            call(mock_after()),
        ])
        mock_from.assert_called_once_with({'bar': 1}, 1)


class TestHelperFunctions(object):
    def test_subscribe_to_events(self):
        config = Mock()
        events.subscribe_to_events(config, 'foo', [1, 2], model=3, field=4)
        config.add_subscriber.assert_has_calls([
            call('foo', 1, model=3, field=4),
            call('foo', 2, model=3, field=4)
        ])


class TestModelClassIs(object):
    def test_wrong_class(self):
        class A(object):
            pass

        predicate = events.ModelClassIs(model=A, config=None)
        event = events.before_index(view=None, model=list)
        assert not predicate(event)

    def test_correct_class(self):
        class A(object):
            pass

        predicate = events.ModelClassIs(model=A, config=None)
        event = events.before_index(view=None, model=A)
        assert predicate(event)

    def test_correct_subclass(self):
        class A(object):
            pass

        class B(A):
            pass

        predicate = events.ModelClassIs(model=A, config=None)
        event = events.before_index(view=None, model=B)
        assert predicate(event)


class TestFieldIsChanged(object):
    def test_field_changed(self):
        predicate = events.FieldIsChanged(field='username', config=None)
        event = events.before_index(
            view=None, model=None,
            fields={'username': 'asd'})
        assert event.field is None
        assert predicate(event)
        assert event.field == 'asd'

    def test_field_not_changed(self):
        predicate = events.FieldIsChanged(field='username', config=None)
        event = events.before_index(
            view=None, model=None,
            fields={'password': 'asd'})
        assert event.field is None
        assert not predicate(event)
        assert event.field is None
