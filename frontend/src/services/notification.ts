import type { Notification } from '../types/notification';
import { notificationApiClient } from './axiosConfig';

// Backend API structure
interface NotificationApiResponse {
  id: number;
  ticket_id: string;
  ticket_title: string;
  ticket_description: string;
  message: string;
  sent_at: string;
  read: boolean;
}

// Adapter function
const adaptNotification = (apiData: NotificationApiResponse): Notification => ({
  id: apiData.id.toString(),
  ticketId: apiData.ticket_id,
  title: apiData.ticket_title || `Ticket #${apiData.ticket_id}`,
  description: apiData.ticket_description,
  message: apiData.message,
  read: apiData.read,
  createdAt: apiData.sent_at,
});

export const notificationsApi = {
  async getNotifications(): Promise<Notification[]> {
    const { data } = await notificationApiClient.get<NotificationApiResponse[]>('/notifications/');
    return data.map(adaptNotification);
  },

  async markAsRead(id: string): Promise<void> {
    await notificationApiClient.patch(`/notifications/${id}/read/`);
  },

  async clearAll(): Promise<void> {
    await notificationApiClient.delete('/notifications/clear/');
  },

  async deleteNotification(id: string): Promise<void> {
    await notificationApiClient.delete(`/notifications/${id}/`);
  },
};
