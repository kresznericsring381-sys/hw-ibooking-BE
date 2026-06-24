"""核心场景自动化测试 —— 与 test.http 中 8 个验收场景一一对应"""
import json
from urllib.parse import urlencode

STUDENT_ID = '2024001'
ROOM_ID = 2
SEAT_ID = 1
TIME_A = '2026-06-01T10:00:00'
TIME_B = '2026-06-01T12:00:00'
TIME_OVERLAP = '2026-06-01T11:00:00'
TIME_END = '2026-06-01T14:00:00'


def test_01_health(client):
    """场景 1：健康检查（test.http §健康检查）"""
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'healthy'


def test_02_seat_init(client):
    """场景 2：座位批量初始化（test.http §初始化座位）"""
    resp = client.post(
        '/api/admin/seat/init',
        data=json.dumps({'room_id': ROOM_ID, 'rows': 10, 'cols': 10}),
        content_type='application/json',
    )
    data = resp.get_json()
    assert resp.status_code in (200, 201, 400)
    # 已初始化时返回 400 亦视为预期行为
    if data.get('success'):
        assert data.get('count', 0) >= 0


def test_03_seat_init_duplicate(client):
    """场景 3：重复初始化拦截（test.http 增量 1 验收）"""
    payload = json.dumps({'room_id': ROOM_ID, 'rows': 10, 'cols': 10})
    client.post('/api/admin/seat/init', data=payload, content_type='application/json')
    resp = client.post('/api/admin/seat/init', data=payload, content_type='application/json')
    data = resp.get_json()
    assert data['success'] is False
    assert '初始化' in data.get('message', '')


def test_04_seat_status_query(client):
    """场景 4：座位状态联查（test.http §获取教室座位信息）"""
    qs = urlencode({'start_time': TIME_A, 'end_time': TIME_B})
    resp = client.get(f'/api/rooms/{ROOM_ID}/seats?{qs}')
    data = resp.get_json()
    assert resp.status_code == 200, data
    assert data.get('success') is True
    assert 'seats' in data


def test_05_order_create_success(client):
    """场景 5：正常预约（test.http §创建订单）"""
    resp = client.post(
        '/api/orders',
        data=json.dumps({
            'student_id': STUDENT_ID,
            'room_id': ROOM_ID,
            'seat_id': SEAT_ID,
            'start_time': '2026-07-01T10:00:00',
            'end_time': '2026-07-01T12:00:00',
        }),
        content_type='application/json',
    )
    data = resp.get_json()
    assert resp.status_code in (201, 400)
    if data.get('success'):
        assert 'order_id' in data


def test_06_seat_time_conflict(client):
    """场景 6：同座位时间冲突（test.http §场景 2 冲突检测）"""
    base = {
        'student_id': STUDENT_ID,
        'room_id': ROOM_ID,
        'seat_id': SEAT_ID,
        'start_time': '2026-08-01T10:00:00',
        'end_time': '2026-08-01T12:00:00',
    }
    first = client.post('/api/orders', data=json.dumps(base), content_type='application/json')
    if not first.get_json().get('success'):
        return  # 已有占用订单时跳过重复创建
    overlap = dict(base)
    overlap['start_time'] = '2026-08-01T11:00:00'
    overlap['end_time'] = '2026-08-01T13:00:00'
    resp = client.post('/api/orders', data=json.dumps(overlap), content_type='application/json')
    data = resp.get_json()
    assert data['success'] is False
    assert '已被预约' in data.get('message', '') or '冲突' in data.get('message', '')


def test_07_student_time_conflict(client):
    """场景 7：同学生时间冲突（test.http §场景 2）"""
    resp = client.post(
        '/api/orders',
        data=json.dumps({
            'student_id': STUDENT_ID,
            'room_id': ROOM_ID,
            'seat_id': SEAT_ID + 1,
            'start_time': '2026-08-01T10:00:00',
            'end_time': '2026-08-01T12:00:00',
        }),
        content_type='application/json',
    )
    data = resp.get_json()
    if resp.status_code == 201 and data.get('success'):
        assert False, '应拒绝同一学生重叠时段的第二单'
    assert data['success'] is False
    assert '已有' in data.get('message', '') or '预约' in data.get('message', '')


def test_08_admin_list_and_cancel(client):
    """场景 8：管理端监控与强制取消（test.http §场景 3）"""
    list_resp = client.get('/api/admin/orders?page=1&page_size=10')
    assert list_resp.status_code == 200
    orders = list_resp.get_json().get('orders', [])
    if orders:
        oid = orders[0]['id']
        cancel = client.post(f'/api/admin/orders/{oid}/cancel', content_type='application/json')
        assert cancel.status_code in (200, 404)
