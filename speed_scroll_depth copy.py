from pywinauto import Desktop
import time
import os
import json


# ============================================================
# 설정
# ============================================================

PROGRAM_TITLE = "document_env"

ROOT_FOLDER = "document_env"

LOCAL_ROOT = r"C:\Users\HP\Downloads\test_scroll_depth"

JSON_FILE = r"C:\Users\HP\Downloads\test_scroll_depth.json"

SKIP_FOLDERS = {
    "휴지통"
}

WAIT_TIME = 0.1

MAX_RETRY = 3

# 스크롤 이동 간격
SCROLL_STEP = 5.0

# 같은 화면이 반복되는 경우 종료하기 위한 횟수
MAX_SAME_SCREEN = 3

APP_PID = None

DOCUMENT_STRUCTURE = None


# ============================================================
# 프로그램 초기 창 찾기
# ============================================================

def find_initial_window():

    desktop = Desktop(backend="uia")

    try:

        window = desktop.window(
            title=PROGRAM_TITLE
        )

        if window.exists():

            print(
                f"프로그램 창 발견: {window.window_text()}"
            )

            return window

    except Exception as e:

        print(
            f"프로그램 창 탐색 실패: {e}"
        )

    return None


# ============================================================
# 프로그램 초기화
# ============================================================

def initialize_app():

    global APP_PID

    window = find_initial_window()

    if window is None:

        print(
            "프로그램 창을 찾을 수 없습니다."
        )

        return False

    try:

        APP_PID = window.process_id()

        print(
            f"프로그램 PID: {APP_PID}"
        )

        return True

    except Exception as e:

        print(
            f"PID를 가져올 수 없습니다: {e}"
        )

        return False


# ============================================================
# 현재 프로그램 창 가져오기
# ============================================================

def get_window():

    global APP_PID

    if APP_PID is None:

        return None

    desktop = Desktop(backend="uia")

    try:

        windows = desktop.windows(
            process=APP_PID
        )

    except Exception:

        return None

    # List가 존재하는 창을 우선적으로 찾음
    for window in windows:

        try:

            lists = window.descendants(
                control_type="List"
            )

            if lists:

                return window

        except Exception:

            pass

    # List를 못 찾으면 첫 번째 창 반환
    if windows:

        return windows[0]

    return None


# ============================================================
# 현재 List 가져오기
# ============================================================

def get_file_list():

    window = get_window()

    if window is None:

        return None

    try:

        lists = window.descendants(
            control_type="List"
        )

        if not lists:

            return None

        return lists[0]

    except Exception:

        return None


# ============================================================
# 파일 / 폴더 타입 확인
# ============================================================

def get_item_type(item):
    try:
        children = item.children()

        for child in children:
            try:
                automation_id = (
                    child.element_info.automation_id
                )

                if automation_id == "System.ItemTypeText":
                    try:
                        return child.get_value()
                    except Exception:
                        return ""

            except Exception:
                continue

    except Exception:
        pass

    return ""


# ============================================================
# 현재 화면의 ListItem 가져오기
# ============================================================

def get_visible_items(file_list):
    if file_list is None:
        return []

    try:
        items = file_list.descendants(
            control_type="ListItem"
        )
    except Exception:
        return []

    result = []

    for item in items:
        try:
            name = item.window_text()

            if not name:
                continue

            # 폴더/파일 판별
            # 확장자를 사용하지 않고 UIA의
            # System.ItemTypeText 값을 사용
            item_type = get_item_type(
                item
            )

            if item_type == "파일 폴더":
                item_kind = "folder"
            else:
                item_kind = "file"

            result.append({
                "name": name,
                "type": item_kind
            })

        except Exception:
            continue

    return result


# ============================================================
# 목록 스크롤바 찾기
# ============================================================

def get_vertical_scrollbar():

    window = get_window()

    if window is None:

        return None

    try:

        scrollbars = window.descendants(
            control_type="ScrollBar"
        )

    except Exception:

        return None

    for scrollbar in scrollbars:

        try:

            automation_id = (
                scrollbar.element_info.automation_id
            )

            if automation_id == "VerticalScrollBar":

                return scrollbar

        except Exception:

            pass

    return None


# ============================================================
# 스크롤바 RangeValue 가져오기
# ============================================================

def get_scroll_range(scrollbar=None):
    if scrollbar is None:
        scrollbar = get_vertical_scrollbar()

    if scrollbar is None:
        return None

    try:
        return scrollbar.iface_range_value
    except Exception:
        return None


# ============================================================
# 스크롤바 현재 위치
# ============================================================

def get_scroll_position(scrollbar=None):
    range_value = get_scroll_range(scrollbar)

    if range_value is None:
        return None

    try:
        return range_value.CurrentValue
    except Exception:
        return None


# ============================================================
# 스크롤바 최댓값
# ============================================================

def get_scroll_maximum(scrollbar=None):
    range_value = get_scroll_range(scrollbar)

    if range_value is None:
        return None

    try:
        return range_value.CurrentMaximum
    except Exception:
        return None


# ============================================================
# 스크롤바 위치 이동
# ============================================================

def set_scroll_position(
    target_position,
    scrollbar=None
):
    if scrollbar is None:
        scrollbar = get_vertical_scrollbar()

    if scrollbar is None:
        print(
            "스크롤바를 찾지 못했습니다."
        )
        return False

    range_value = get_scroll_range(scrollbar)

    if range_value is None:
        print(
            "스크롤바 RangeValue를 가져오지 못했습니다."
        )
        return False

    try:
        minimum = range_value.CurrentMinimum
        maximum = range_value.CurrentMaximum

        target_position = max(
            minimum,
            min(
                target_position,
                maximum
            )
        )

        current = range_value.CurrentValue

        # 이미 해당 위치라면 성공 처리
        if abs(current - target_position) < 0.5:
            return True

        range_value.SetValue(
            target_position
        )

        time.sleep(
            WAIT_TIME
        )

        after = range_value.CurrentValue

        # 실제 위치가 변했는지만 확인
        if abs(after - current) >= 0.5:
            return True

        return False

    except Exception as e:
        print(
            f"스크롤 이동 오류: {e}"
        )
        return False


# ============================================================
# 목록 최상단 이동
# ============================================================

def scroll_to_top(scrollbar=None):
    if scrollbar is None:
        scrollbar = get_vertical_scrollbar()

    range_value = get_scroll_range(scrollbar)

    if range_value is None:
        return False

    try:
        minimum = range_value.CurrentMinimum
        current = range_value.CurrentValue

        print(
            f"목록 최상단 이동: "
            f"{current:.1f} → {minimum:.1f}"
        )

        range_value.SetValue(
            minimum
        )

        time.sleep(
            WAIT_TIME
        )

        return True

    except Exception as e:
        print(
            f"최상단 이동 실패: {e}"
        )
        return False


# ============================================================
# 화면 항목을 일반 Python 데이터로 변환
# ============================================================

def collect_visible_items(file_list):
    items = get_visible_items(
        file_list
    )

    result = []

    for item in items:
        name = item["name"]

        if not name:
            continue

        result.append({
            "name": name,
            "type": item["type"]
        })

    return result


# ============================================================
# 현재 폴더 전체 항목 수집
# ============================================================

def get_all_items():
    print()
    print(
        "현재 폴더 전체 항목 수집 시작"
    )

    all_items = {}

    # --------------------------------------------------------
    # List와 스크롤바를 한 번만 가져옴
    # --------------------------------------------------------

    file_list = get_file_list()

    if file_list is None:
        print(
            "파일 목록을 찾을 수 없습니다."
        )
        return []

    scrollbar = get_vertical_scrollbar()

    if scrollbar is None:
        print(
            "목록 스크롤바를 찾을 수 없습니다."
        )
        return collect_visible_items(
            file_list
        )

    # --------------------------------------------------------
    # 최상단 이동
    # --------------------------------------------------------

    if not scroll_to_top(scrollbar):
        print(
            "목록 최상단 이동 실패"
        )

    # --------------------------------------------------------
    # 스크롤 최대값 확인
    # --------------------------------------------------------

    maximum = get_scroll_maximum(
        scrollbar
    )

    if maximum is None:
        print(
            "스크롤 최대값을 확인할 수 없습니다."
        )
        return collect_visible_items(
            file_list
        )

    print(
        f"스크롤 범위: 0 ~ {maximum}"
    )

    # --------------------------------------------------------
    # 반복 수집
    # --------------------------------------------------------

    loop_count = 0
    previous_position = None
    same_screen_count = 0

    while True:
        loop_count += 1

        # ----------------------------------------------------
        # 현재 화면 수집
        # ----------------------------------------------------

        visible_items = collect_visible_items(
            file_list
        )

        new_count = 0

        for item in visible_items:
            name = item["name"]

            if name not in all_items:
                all_items[name] = {
                    "name": name,
                    "type": item["type"]
                }

                new_count += 1

        # ----------------------------------------------------
        # 현재 위치 확인
        # ----------------------------------------------------

        actual_position = get_scroll_position(
            scrollbar
        )

        if actual_position is None:
            actual_position = 0.0

        print(
            f"[{loop_count:03d}] "
            f"위치: {actual_position:.1f} "
            f"/ 화면: {len(visible_items)}개 "
            f"/ 전체 누적: {len(all_items)}개 "
            f"/ 신규: {new_count}개"
        )

        # ----------------------------------------------------
        # 같은 위치가 반복되는지 확인
        # ----------------------------------------------------

        if (
            previous_position is not None
            and abs(
                actual_position
                - previous_position
            ) < 0.5
        ):
            same_screen_count += 1
        else:
            same_screen_count = 0

        previous_position = actual_position

        # ----------------------------------------------------
        # 최대 위치 도달
        # ----------------------------------------------------

        if actual_position >= maximum - 0.5:
            print(
                "스크롤 최하단 도달"
            )
            break

        # ----------------------------------------------------
        # 다음 위치 계산
        # ----------------------------------------------------

        next_target = min(
            actual_position + SCROLL_STEP,
            maximum
        )

        # ----------------------------------------------------
        # 스크롤
        # ----------------------------------------------------

        success = set_scroll_position(
            next_target,
            scrollbar
        )

        if not success:
            print(
                "스크롤 위치 변경 실패"
            )

            # 최대 위치라면 한 번 더 최하단 수집
            if next_target >= maximum:
                set_scroll_position(
                    maximum,
                    scrollbar
                )

                final_items = collect_visible_items(
                    file_list
                )

                for item in final_items:
                    name = item["name"]

                    if name not in all_items:
                        all_items[name] = {
                            "name": name,
                            "type": item["type"]
                        }

            break

        # ----------------------------------------------------
        # 같은 위치가 반복되면 종료
        # ----------------------------------------------------

        if same_screen_count >= MAX_SAME_SCREEN:
            print(
                "같은 화면이 반복되어 "
                "수집을 종료합니다."
            )
            break

        # ----------------------------------------------------
        # 무한 반복 방지
        # ----------------------------------------------------

        if loop_count > 1000:
            print(
                "최대 반복 횟수 초과"
            )
            break

    # --------------------------------------------------------
    # 결과
    # --------------------------------------------------------

    result = list(
        all_items.values()
    )

    print()
    print(
        f"전체 항목 수집 완료: {len(result)}개"
    )

    return result


# ============================================================
# 현재 폴더 목록 출력
# ============================================================

def print_items(
    path,
    items
):

    print()
    print(
        "=" * 70
    )

    print(
        f"현재 위치: {path}"
    )

    print(
        "=" * 70
    )

    if not items:

        print(
            "(빈 폴더)"
        )

    for item in items:

        if item["type"] == "folder":

            print(
                f"[폴더] {item['name']}"
            )

        else:

            print(
                f"[파일] {item['name']}"
            )

    print(
        "=" * 70
    )

    print(
        f"총 항목: {len(items)}개"
    )

    print(
        "=" * 70
    )


# ============================================================
# 현재 화면에서 특정 폴더 찾기
# ============================================================

def find_folder(
    folder_name
):

    file_list = get_file_list()

    if file_list is None:

        return None

    try:

        items = file_list.descendants(
            control_type="ListItem"
        )

        for item in items:

            try:

                name = item.window_text()

                if name != folder_name:

                    continue

                item_type = get_item_type(
                    item
                )

                if item_type == "파일 폴더":

                    return item

            except Exception:

                pass

    except Exception:

        pass

    return None


# ============================================================
# 현재 폴더에서 특정 폴더 진입
# ============================================================

def enter_folder(
    folder_name
):

    print()
    print(
        f">>> '{folder_name}' 진입 시도"
    )

    for retry in range(
        1,
        MAX_RETRY + 1
    ):

        try:

            # ------------------------------------------------
            # 폴더가 현재 화면에 있는지 확인
            # ------------------------------------------------

            folder = find_folder(
                folder_name
            )

            if folder is None:

                print(
                    f"폴더를 찾지 못함 "
                    f"(시도 {retry}/{MAX_RETRY})"
                )

                time.sleep(
                    WAIT_TIME
                )

                continue

            # ------------------------------------------------
            # 클릭
            # ------------------------------------------------

            folder.click_input()

            time.sleep(
                WAIT_TIME
            )

            # ------------------------------------------------
            # Enter
            # ------------------------------------------------

            window = get_window()

            if window is None:

                print(
                    "프로그램 창을 찾지 못함"
                )

                continue

            window.set_focus()

            window.type_keys(
                "{ENTER}"
            )

            time.sleep(
                WAIT_TIME
            )

            # ------------------------------------------------
            # 새로운 List 확인
            # ------------------------------------------------

            new_list = get_file_list()

            if new_list is not None:

                print(
                    f">>> '{folder_name}' 진입 완료"
                )

                return True

        except Exception as e:

            print(
                f"진입 오류: {e}"
            )

        print(
            f"재시도합니다. "
            f"({retry}/{MAX_RETRY})"
        )

        time.sleep(
            WAIT_TIME
        )

    print(
        f">>> '{folder_name}' 진입 실패"
    )

    return False


# ============================================================
# 부모 폴더로 이동
# ============================================================

def get_list_state():

    window = get_window()

    if window is None:
        return None, ()

    try:
        title = window.window_text()
    except Exception:
        title = ""

    try:
        file_list = get_file_list()

        if file_list is None:
            return title, ()

        items = file_list.descendants(
            control_type="ListItem"
        )

        names = []

        for item in items:
            try:
                name = item.window_text()

                if name:
                    names.append(name)
            except Exception:
                continue

        return title, tuple(names)

    except Exception:
        return title, ()


# ============================================================
# 부모 폴더 목록 갱신 대기
# ============================================================

def wait_for_parent_list(
    previous_title,
    previous_names,
    timeout=0.6
):

    start_time = time.time()

    while time.time() - start_time < timeout:

        current_title, current_names = get_list_state()

        # 부모 폴더는 현재 탐색 중인 폴더의 상위 폴더이므로
        # 정상적으로 돌아왔다면 목록에 최소 1개 이상의 항목이 있어야 함
        if current_names:

            # 창 제목이 바뀐 경우를 가장 우선적으로 확인
            if (
                previous_title
                and current_title
                and current_title != previous_title
            ):
                return True

            # 제목이 동일한 프로그램이라면 목록 변화로 확인
            if current_names != previous_names:
                return True

        time.sleep(0.03)

    return False


# ============================================================
# 부모 폴더로 이동
# ============================================================

def go_back():

    print(
        "<<< 부모 폴더로 이동"
    )

    for retry in range(
        1,
        MAX_RETRY + 1
    ):

        window = get_window()

        if window is None:

            print(
                "프로그램 창을 찾을 수 없음"
            )

            time.sleep(
                WAIT_TIME
            )

            continue

        try:

            # ------------------------------------------------
            # 뒤로가기 전 현재 화면 상태 저장
            # ------------------------------------------------

            previous_title, previous_names = (
                get_list_state()
            )

            window.set_focus()

            window.type_keys(
                "%{LEFT}"
            )

            # ------------------------------------------------
            # 부모 폴더 목록이 실제로 갱신될 때까지 대기
            # ------------------------------------------------

            if wait_for_parent_list(
                previous_title,
                previous_names
            ):

                print(
                    "<<< 부모 폴더 이동 완료"
                )

                return True

            print(
                "부모 폴더 목록 갱신 확인 실패"
            )

        except Exception as e:

            print(
                f"뒤로가기 오류: {e}"
            )

        print(
            f"뒤로가기 재시도 "
            f"({retry}/{MAX_RETRY})"
        )

        time.sleep(
            WAIT_TIME
        )

    print(
        "<<< 부모 폴더 이동 실패"
    )

    return False


# ============================================================
# 로컬 폴더 생성
# ============================================================

def create_local_folder(
    path
):

    try:

        os.makedirs(
            path,
            exist_ok=True
        )

        print(
            f"[폴더 생성] {path}"
        )

        return True

    except Exception as e:

        print(
            f"[폴더 생성 실패] {path}"
        )

        print(
            f"    오류: {e}"
        )

        return False


# ============================================================
# 로컬 빈 파일 생성
# ============================================================

def create_local_file(
    path
):

    try:

        if not os.path.exists(path):

            with open(
                path,
                "wb"
            ):
                pass

            print(
                f"[파일 생성] {path}"
            )

        else:

            print(
                f"[파일 존재] {path}"
            )

        return True

    except Exception as e:

        print(
            f"[파일 생성 실패] {path}"
        )

        print(
            f"    오류: {e}"
        )

        return False


# ============================================================
# 현재 폴더의 구조를 로컬에 생성
# ============================================================

def copy_current_structure(
    items,
    local_path
):

    if not create_local_folder(
        local_path
    ):

        return False

    for item in items:

        name = item["name"]

        item_type = item["type"]

        # ----------------------------------------------------
        # 휴지통 제외
        # ----------------------------------------------------

        if (
            item_type == "folder"
            and name in SKIP_FOLDERS
        ):

            print(
                f"[건너뜀] {name}"
            )

            continue

        # ----------------------------------------------------
        # 폴더
        # ----------------------------------------------------

        if item_type == "folder":

            folder_path = os.path.join(
                local_path,
                name
            )

            create_local_folder(
                folder_path
            )

        # ----------------------------------------------------
        # 파일
        # ----------------------------------------------------

        else:

            file_path = os.path.join(
                local_path,
                name
            )

            create_local_file(
                file_path
            )

    return True


# ============================================================
# JSON children 생성
# ============================================================

def build_json_children(
    items
):

    children = []

    for item in items:

        name = item["name"]

        item_type = item["type"]

        # 휴지통 제외
        if (
            item_type == "folder"
            and name in SKIP_FOLDERS
        ):

            continue

        # 폴더
        if item_type == "folder":

            children.append({

                "name": name,

                "type": "folder",

                "children": []

            })

        # 파일
        else:

            children.append({

                "name": name,

                "type": "file"

            })

    return children


# ============================================================
# JSON 저장
# ============================================================

def save_json(
    structure
):

    try:

        json_directory = os.path.dirname(
            JSON_FILE
        )

        if json_directory:

            os.makedirs(
                json_directory,
                exist_ok=True
            )

        temp_file = JSON_FILE + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                structure,
                f,
                ensure_ascii=False,
                indent=4
            )

        os.replace(
            temp_file,
            JSON_FILE
        )

        print(
            f"[JSON 저장 완료] {JSON_FILE}"
        )

        return True

    except Exception as e:

        print(
            f"[JSON 저장 실패] {e}"
        )

        return False


# ============================================================
# JSON에서 하위 폴더 노드 찾기
# ============================================================

def find_json_folder_node(
    parent_node,
    folder_name
):

    for child in parent_node.get(
        "children",
        []
    ):

        if (
            child.get("type") == "folder"
            and child.get("name") == folder_name
        ):

            return child

    return None


# ============================================================
# 현재 폴더 탐색
# ============================================================

def scan_folder(
    path,
    local_path,
    structure_node
):

    print()
    print(
        "############################################################"
    )

    print(
        f"탐색 시작: {path}"
    )

    print(
        "############################################################"
    )

    # --------------------------------------------------------
    # 현재 폴더 전체 항목 수집
    # --------------------------------------------------------

    items = get_all_items()

    if items is None:

        print(
            f"현재 폴더 탐색 실패: {path}"
        )

        return False

    # --------------------------------------------------------
    # 휴지통 제외
    # --------------------------------------------------------

    filtered_items = []

    for item in items:

        if (
            item["type"] == "folder"
            and item["name"] in SKIP_FOLDERS
        ):

            print(
                f"[탐색 제외] {item['name']}"
            )

            continue

        filtered_items.append(
            item
        )

    items = filtered_items

    # --------------------------------------------------------
    # 현재 목록 출력
    # --------------------------------------------------------

    print_items(
        path,
        items
    )

    # --------------------------------------------------------
    # 로컬 구조 생성
    # --------------------------------------------------------

    copy_current_structure(
        items,
        local_path
    )

    # --------------------------------------------------------
    # JSON 갱신
    # --------------------------------------------------------

    structure_node["children"] = (
        build_json_children(
            items
        )
    )

    # --------------------------------------------------------
    # 중간 저장
    # --------------------------------------------------------

    save_json(
        DOCUMENT_STRUCTURE
    )

    # --------------------------------------------------------
    # 하위 폴더 이름 저장
    # --------------------------------------------------------

    folder_names = []

    for item in items:

        if item["type"] != "folder":

            continue

        folder_name = item["name"]

        if folder_name in SKIP_FOLDERS:

            continue

        folder_names.append(
            folder_name
        )

    # --------------------------------------------------------
    # 하위 폴더 탐색
    # --------------------------------------------------------

    for folder_name in folder_names:

        print()
        print(
            "------------------------------------------------------------"
        )

        print(
            f"하위 폴더 처리: {folder_name}"
        )

        print(
            "------------------------------------------------------------"
        )

        child_node = find_json_folder_node(
            structure_node,
            folder_name
        )

        if child_node is None:

            print(
                f"JSON 폴더 노드를 찾을 수 없음: {folder_name}"
            )

            continue

        child_local_path = os.path.join(
            local_path,
            folder_name
        )

        child_path = (
            path
            + "\\"
            + folder_name
        )

        # ----------------------------------------------------
        # 폴더 진입
        # ----------------------------------------------------

        success = enter_folder(
            folder_name
        )

        if not success:

            print(
                f"폴더 진입 실패: {child_path}"
            )

            continue

        # ----------------------------------------------------
        # 하위 폴더 탐색
        # ----------------------------------------------------

        try:

            scan_folder(
                child_path,
                child_local_path,
                child_node
            )

        except Exception as e:

            print()
            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )

            print(
                f"하위 폴더 탐색 중 오류: {child_path}"
            )

            print(
                f"오류 내용: {e}"
            )

            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )

            save_json(
                DOCUMENT_STRUCTURE
            )

        # ----------------------------------------------------
        # 부모 폴더 복귀
        # ----------------------------------------------------

        back_success = go_back()

        if not back_success:

            print()
            print(
                "부모 폴더 복귀 실패"
            )

            print(
                f"현재 처리 폴더: {child_path}"
            )

            time.sleep(
                WAIT_TIME * 2
            )

    # --------------------------------------------------------
    # 폴더 완료
    # --------------------------------------------------------

    save_json(
        DOCUMENT_STRUCTURE
    )

    print()
    print(
        f"탐색 완료: {path}"
    )

    return True


# ============================================================
# 메인
# ============================================================

print()
print(
    "============================================================"
)

print(
    "문서중앙화 탐색 + 스크롤 전체 수집 + "
    "로컬 구조 복제 + JSON 생성"
)

print(
    "============================================================"
)

print()

print(
    f"프로그램 창: {PROGRAM_TITLE}"
)

print(
    f"시작 위치: {ROOT_FOLDER}"
)

print(
    f"로컬 복제 위치: {LOCAL_ROOT}"
)

print(
    f"JSON 저장 위치: {JSON_FILE}"
)

print(
    f"스크롤 이동 간격: {SCROLL_STEP}"
)

print(
    f"탐색 제외 폴더: {', '.join(SKIP_FOLDERS)}"
)

print()


# ============================================================
# 프로그램 초기화
# ============================================================

if not initialize_app():

    print()
    print(
        "프로그램 초기화 실패"
    )

    print(
        "탐색을 종료합니다."
    )

else:

    # --------------------------------------------------------
    # 로컬 루트 생성
    # --------------------------------------------------------

    create_local_folder(
        LOCAL_ROOT
    )

    # --------------------------------------------------------
    # JSON 초기 구조
    # --------------------------------------------------------

    DOCUMENT_STRUCTURE = {

        "name": ROOT_FOLDER,

        "type": "folder",

        "children": []

    }

    # --------------------------------------------------------
    # 최초 JSON 저장
    # --------------------------------------------------------

    save_json(
        DOCUMENT_STRUCTURE
    )

    # --------------------------------------------------------
    # 전체 탐색
    # --------------------------------------------------------

    try:

        scan_folder(

            ROOT_FOLDER,

            LOCAL_ROOT,

            DOCUMENT_STRUCTURE

        )

    except KeyboardInterrupt:

        print()
        print(
            "사용자가 탐색을 중단했습니다."
        )

        save_json(
            DOCUMENT_STRUCTURE
        )

    except Exception as e:

        print()
        print(
            "============================================================"
        )

        print(
            "전체 탐색 중 예외 발생"
        )

        print(
            f"오류: {e}"
        )

        print(
            "============================================================"
        )

        save_json(
            DOCUMENT_STRUCTURE
        )


# ============================================================
# 종료
# ============================================================

print()
print(
    "============================================================"
)

print(
    "탐색 / 복제 / JSON 생성 종료"
)

print(
    "============================================================"
)

print()

print(
    "로컬 복제 위치:"
)

print(
    LOCAL_ROOT
)

print()

print(
    "JSON 파일:"
)

print(
    JSON_FILE
)

print()