import 'package:djc_example/jsonbase.dart';
import 'package:djc_example/example.dart';
import 'package:test/test.dart';

/// convert to map and back to T
T mapRoundtrip<T extends JsonBase>(fromMap, T t) => fromMap(t.toMap());

/// convert to json and back to T
T jsonRoundtrip<T extends JsonBase>(fromJson, T t) => fromJson(t.toJson());

/// common tests for simple + complex classes
void commonTests<T extends JsonBase>(fromMap, fromJson, List<String> fields, T t) {
  test('roundtrip_equal', () {
    expect(t, mapRoundtrip(fromMap, t));
    expect(t, jsonRoundtrip(fromJson, t));
    expect(t.hashCode, jsonRoundtrip(fromJson, t).hashCode);
  });

  test('copy_equal', () {
    expect(t, t.copy());
    expect(t.copy(), jsonRoundtrip(fromJson, t));
    expect(t.hashCode, t.copy().hashCode);
  });

  test('copy_hashcodes', () {
    final copy = t.copy();
    for (final field in fields) {
      expect(copy.getAttr(field).hashCode, t.getAttr(field).hashCode, reason: field);
    }
  });
}

void main() {
  test('fromMap_null_field', () {
    expect(NullItem.fromMap({'item': null}), NullItem(null));
    expect(NullItem.fromMap({}), NullItem(null));
  });

  group('literal_collection', () {
    final strlist = StrList(["a", "b"], {"x": "y"});

    commonTests((x) => StrList.fromMap(x), (x) => StrList.fromJson(x), StrList.djc__fields, strlist);

    test('equality', () {
      expect(identical(strlist.strlist, strlist.copy().strlist), false);
      expect(strlist, strlist.copy());
    });

    test('fromMap', () {
      expect(strlist, mapRoundtrip((x) => StrList.fromMap(x), strlist));
      expect(strlist, jsonRoundtrip((x) => StrList.fromJson(x), strlist));
    });
  });

  final item = Item(1, "one");
  group('simple_Item', () {
    commonTests((x) => Item.fromMap(x), (x) => Item.fromJson(x), Item.djc__fields, item);

    test('value_equality', () {
      expect(item, item);
      expect(item, Item(1, "one"));
      expect(item == Item(1, "two"), false);
    });

    test('get_set', () {
      final item = Item(2, "two");
      expect(item.getAttr('a'), 2);
      item.setAttr('a', 3);
      expect(item.getAttr('a'), 3);
    });
  });

  group('complex_Msg', () {
    final msg = Msg(
      "12345",
      null,
      item,
      [Item(2, "two")],
      {"x": Item(3, "three")},
      {"y": Item(4, "four")},
    );

    commonTests((x) => Msg.fromMap(x), (x) => Msg.fromJson(x), Msg.djc__fields, msg);
  });

  // todo: in deep copy, make sure collections, collection items, and JsonBase attrs are equal but not same instance
}
