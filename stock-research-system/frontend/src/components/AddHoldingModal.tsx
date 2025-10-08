import React, { useState } from 'react';
import { Modal, Form, Input, InputNumber, DatePicker, Button, message } from 'antd';
import axios from 'axios';
import dayjs from 'dayjs';
import { theme } from '../styles/theme';

interface AddHoldingModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  userEmail: string;
}

const AddHoldingModal: React.FC<AddHoldingModalProps> = ({ visible, onCancel, onSuccess, userEmail }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const payload = {
        symbol: values.symbol.toUpperCase(),
        shares: values.shares,
        purchase_price: values.purchase_price,
        purchase_date: values.purchase_date.format('YYYY-MM-DD'),
        notes: values.notes || ''
      };

      const response = await axios.post(
        `http://localhost:8000/api/v1/portfolio/${userEmail}/holdings`,
        payload
      );

      if (response.data.status === 'success') {
        message.success(response.data.message);
        form.resetFields();
        onSuccess();
      }
    } catch (error: any) {
      console.error('Error adding holding:', error);
      message.error(error.response?.data?.detail || 'Failed to add holding');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="Add Holding to Portfolio"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={500}
      styles={{
        mask: { backgroundColor: 'rgba(0, 0, 0, 0.7)' }
      }}
    >
      <div style={{ backgroundColor: theme.colors.background.elevated, padding: '24px', borderRadius: 8 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          requiredMark={false}
        >
          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Stock Symbol</span>}
            name="symbol"
            rules={[
              { required: true, message: 'Please enter stock symbol' },
              { pattern: /^[A-Za-z]+$/, message: 'Only letters allowed' }
            ]}
          >
            <Input
              placeholder="e.g., AAPL"
              maxLength={5}
              style={{
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Number of Shares</span>}
            name="shares"
            rules={[{ required: true, message: 'Please enter number of shares' }]}
          >
            <InputNumber
              min={0.01}
              step={1}
              placeholder="e.g., 100"
              style={{
                width: '100%',
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Purchase Price per Share</span>}
            name="purchase_price"
            rules={[{ required: true, message: 'Please enter purchase price' }]}
          >
            <InputNumber
              min={0.01}
              step={0.01}
              precision={2}
              prefix="$"
              placeholder="e.g., 150.00"
              style={{
                width: '100%',
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Purchase Date</span>}
            name="purchase_date"
            rules={[{ required: true, message: 'Please select purchase date' }]}
          >
            <DatePicker
              style={{
                width: '100%',
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
              format="YYYY-MM-DD"
              disabledDate={(current) => current && current > dayjs().endOf('day')}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Notes (Optional)</span>}
            name="notes"
          >
            <Input.TextArea
              placeholder="e.g., Purchased based on AI recommendation"
              rows={3}
              maxLength={200}
              style={{
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
            />
          </Form.Item>

          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 24 }}>
            <Button
              onClick={onCancel}
              style={{
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.secondary
              }}
            >
              Cancel
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              style={{
                background: theme.colors.gradient.primary,
                border: 'none',
                color: '#000',
                fontWeight: 600
              }}
            >
              Add to Portfolio
            </Button>
          </div>
        </Form>
      </div>
    </Modal>
  );
};

export default AddHoldingModal;
