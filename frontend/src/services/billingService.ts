import axiosInstance from './axiosInstance';

export interface Invoice {
  id: string;
  amount: number;
  plan: string;
  status: 'paid' | 'unpaid' | 'failed';
  payment_gateway: 'stripe' | 'razorpay';
  invoice_url: string;
  created_at: string;
}

export async function fetchInvoices(): Promise<{ invoices: Invoice[] }> {
  const response = await axiosInstance.get('/billing/invoices');
  return response.data;
}

export async function triggerCheckout(planId: string, gateway: 'stripe' | 'razorpay'): Promise<{ success: boolean; checkout_url: string }> {
  const response = await axiosInstance.post('/billing/checkout', { plan_id: planId, gateway });
  return response.data;
}
