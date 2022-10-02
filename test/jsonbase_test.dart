import 'package:djc_example/jsonbase.dart';
import 'package:test/test.dart';

void main() {
  group('listEqual', () {
    final List<int> left = [1, 2];

    test('same', () {
      expect(listEqual(left, [1, 2]), true);
    });

    test('differ_by_length', () {
      expect(listEqual(left, [1, 2, 3]), false);
      expect(listEqual(left, [1]), false);
    });

    test('differ_by_value', () {
      expect(listEqual(left, [2, 1]), false);
    });

    test('null', () {
      expect(listEqual(left, null), false);
      expect(listEqual(null, null), true);
    });
  });

  group('mapEqual', () {
    final Map<String, int> left = {"a": 1, "b": 2};

    test('same', () {
      expect(mapEqual(left, {"a": 1, "b": 2}), true);
    });

    test('differ_by_length', () {
      expect(mapEqual(left, {"a": 1, "b": 2, "c": 3}), false);
      expect(mapEqual(left, {"a": 1}), false);
    });

    test('differ_by_value', () {
      expect(mapEqual(left, {"a": 1, "b": 3}), false);
    });

    test('null', () {
      expect(mapEqual(left, null), false);
      expect(mapEqual(null, null), true);
    });
  });

  group('collection_hashes', () {
    test('list', () {
      final base = [1, 2];
      expect(hashcodeList(base), hashcodeList([1, 2]));
      expect(base.hashCode, base.hashCode);
      expect(base.hashCode == [1, 2].hashCode, false);
      expect(hashcodeList(base) == hashcodeList([2, 3]), false);
    });

    test('map', () {
      final base = {"a": 1, "b": 2};
      expect(hashcodeMap(base), hashcodeMap({"a": 1, "b": 2}));
      expect(base.hashCode, base.hashCode);
      expect(base.hashCode == {"a": 1, "b": 2}.hashCode, false);
      expect(hashcodeMap(base) == hashcodeMap({"a": 1, "b": 3}), false);
    });
  });

  // todo: nested collections like List<List<int>>, Map<String, List<int>>
}
