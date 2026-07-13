import express from 'express';
import { login, logout, refresh, getMe, getPermissions, forgotPassword, resetPassword } from '../controllers/authController.js';
import { authMiddleware } from '../middleware/authMiddleware.js';

const router = express.Router();

router.post('/login', login);
router.post('/logout', authMiddleware, logout);
router.post('/refresh', refresh);
router.get('/me', authMiddleware, getMe);
router.get('/permissions', authMiddleware, getPermissions);
router.post('/forgot-password', forgotPassword);
router.post('/reset-password', resetPassword);

export default router;
