import re

class CartSorter:
    @staticmethod
    def sort_by_call_number(books: list) -> list:
        """
        도서 리스트를 청구기호 순서대로 정렬하여 최적의 서가 반납 동선을 계산합니다.
        books: [{'title': str, 'call_number': str, 'shelf_location': str}, ...]
        """
        def extract_sort_key(book):
            call_num = book.get('call_number', '').strip()
            if not call_num:
                return (999.9, "zzz")

            # 1. 청구기호 앞부분의 분류번호(숫자) 추출 (예: '813.6 홍12ㄱ' -> '813.6')
            match = re.match(r'([0-9.]+)', call_num)
            if match:
                try:
                    num_part = float(match.group(1))
                except ValueError:
                    num_part = 999.9
                text_part = call_num[match.end():].strip()
            else:
                num_part = 999.9
                text_part = call_num

            # (분류번호 숫자 크기 순, 저자기호 문자열 순) 튜플 반환
            return (num_part, text_part)

        return sorted(books, key=extract_sort_key)