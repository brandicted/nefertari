from mock import Mock

from nefertari.utils import data as dutils


class DummyModel(dict):
    def to_dict(self, *args, **kwargs):
        return self


class TestDataUtils(object):

    def test_data_proxy_not_model(self):
        proxy = dutils.DataProxy({'foo': 'bar'})
        data = proxy.to_dict()
        assert data == {'foo': 'bar'}

    def test_data_proxy_not_model_keys(self):
        proxy = dutils.DataProxy({'foo': 'bar', 'id': 1})
        data = proxy.to_dict(_keys=['foo'])
        assert data == {'foo': 'bar'}

    def test_data_proxy_model(self):
        obj = DummyModel({'foo1': 'bar1'})
        proxy = dutils.DataProxy({'foo': obj})
        data = proxy.to_dict()
        assert data == {'foo': {'foo1': 'bar1'}}

    def test_data_proxy_model_keys(self):
        obj = DummyModel({'foo1': 'bar1'})
        proxy = dutils.DataProxy({'foo': obj, 'id': 1})
        data = proxy.to_dict(_keys=['foo'])
        assert data == {'foo': {'foo1': 'bar1'}}

    def test_data_proxy_model_no_depth(self):
        obj = DummyModel({'foo1': 'bar1'})
        proxy = dutils.DataProxy({'foo': obj})
        data = proxy.to_dict(_depth=0)
        assert data == {'foo': obj}

    def test_data_proxy_model_sequence(self):
        obj = DummyModel({'foo1': 'bar1'})
        proxy = dutils.DataProxy({'foo': [obj]})
        data = proxy.to_dict()
        assert data == {'foo': [{'foo1': 'bar1'}]}

    def test_dict2obj_regular_value(self):
        obj = dutils.dict2obj({'_type': 'Foo', 'foo': 'bar', 'baz': 1})
        assert isinstance(obj, dutils.DataProxy)
        assert obj.foo == 'bar'
        assert obj.baz == 1

    def test_dict2obj_dict_value(self):
        obj = dutils.dict2obj({'_type': 'Foo', 'foo': {'baz': 1}})
        assert isinstance(obj, dutils.DataProxy)
        assert isinstance(obj.foo, dutils.DataProxy)
        assert obj.foo.baz == 1

    def test_dict2obj_list_value(self):
        obj = dutils.dict2obj({'_type': 'Foo', 'foo': [{'baz': 1}]})
        assert isinstance(obj, dutils.DataProxy)
        assert isinstance(obj.foo, list)
        assert len(obj.foo) == 1
        assert isinstance(obj.foo[0], dutils.DataProxy)
        assert obj.foo[0].baz == 1

    def test_to_objs(self):
        collection = dutils.to_objs([{'foo': 'bar', '_type': 'Foo'}])
        assert len(collection) == 1
        assert isinstance(collection[0], dutils.DataProxy)
        assert collection[0].foo == 'bar'

    def test_to_dicts_regular_case(self):
        collection = [DummyModel({'foo': 'bar'})]
        dicts = dutils.to_dicts(collection)
        assert dicts == [{'foo': 'bar'}]

    def test_to_dicts_with_key(self):
        collection = [DummyModel({'foo': 'bar', 'id': '1'})]
        dicts = dutils.to_dicts(collection, key=lambda d: {'super': d['foo']})
        assert dicts == [{'super': 'bar'}]

    def test_to_dicts_attr_error(self):
        obj = DummyModel({'foo': 'bar'})
        dicts = dutils.to_dicts([obj, {'a': 'b'}])
        assert dicts == [obj, {'a': 'b'}]

    def test_to_dicts_type_error(self):
        def key(d):
            raise TypeError()
        obj = DummyModel({'foo': 'bar'})
        dicts = dutils.to_dicts([obj], key=key)
        assert dicts == [obj]

    def test_obj2dict_dict(self):
        assert dutils.obj2dict({'foo': 'bar'}) == {'foo': 'bar'}

    def test_obj2dict_list(self):
        assert dutils.obj2dict([{'foo': 'bar'}]) == [{'foo': 'bar'}]

    def test_obj2dict_object(self):
        class A(object):
            pass
        obj = A()
        obj.foo = 'bar'
        assert dutils.obj2dict(obj) == {'foo': 'bar'}

    def test_obj2dict_object_classkey(self):
        class A(object):
            pass
        obj = A()
        obj.foo = 'bar'
        assert dutils.obj2dict(obj, classkey='kls') == {
            'foo': 'bar', 'kls': 'A'}

    def test_obj2dict_simple_types(self):
        assert dutils.obj2dict(1) == 1
        assert dutils.obj2dict('foo') == 'foo'
        assert dutils.obj2dict(None) is None


class TestFieldData(object):

    def test_init(self):
        obj = dutils.FieldData(name='foo', new_value=1, params={})
        assert obj.name == 'foo'
        assert obj.new_value == 1
        assert obj.params == {}

    def test_repr(self):
        obj = dutils.FieldData(name='foo', new_value=1, params={})
        assert str(obj) == '<FieldData: foo>'

    def test_from_dict_model_provided(self):
        model = Mock()
        model.get_field_params.return_value = {'foo': 1}
        data = {'username': 'admin'}
        result = dutils.FieldData.from_dict(data, model)
        assert list(result.keys()) == ['username']
        field = result['username']
        assert isinstance(field, dutils.FieldData)
        assert field.name == 'username'
        assert field.new_value == 'admin'
        assert field.params == {'foo': 1}
        model.get_field_params.assert_called_once_with('username')
