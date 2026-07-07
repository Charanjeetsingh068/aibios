import React, { useState } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  SafeAreaView, 
  ScrollView, 
  TouchableOpacity, 
  StatusBar 
} from 'react-native';
import { COLORS, SPACING, BORDER_RADIUS, TYPOGRAPHY } from './src/theme/tokens';

export default function App() {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const theme = isDarkMode ? COLORS.dark : COLORS.light;

  const styles = StyleSheet.create({
    safeArea: {
      flex: 1,
      backgroundColor: theme.bgPrimary,
    },
    container: {
      padding: SPACING.space4,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: SPACING.space6,
      paddingVertical: SPACING.space2,
    },
    headerTitle: {
      fontSize: TYPOGRAPHY.sizes.xl,
      fontWeight: TYPOGRAPHY.weights.bold,
      color: theme.textPrimary,
    },
    headerSubtitle: {
      fontSize: TYPOGRAPHY.sizes.xs,
      color: theme.textTertiary,
    },
    themeBtn: {
      paddingHorizontal: SPACING.space3,
      paddingVertical: SPACING.space2,
      borderRadius: BORDER_RADIUS.full,
      backgroundColor: theme.bgTertiary,
      borderWidth: 1,
      borderColor: theme.borderColor,
    },
    themeBtnText: {
      fontSize: TYPOGRAPHY.sizes.xs,
      color: theme.textSecondary,
      fontWeight: TYPOGRAPHY.weights.medium,
    },
    card: {
      backgroundColor: theme.bgSecondary,
      borderRadius: BORDER_RADIUS.md,
      padding: SPACING.space4,
      marginBottom: SPACING.space4,
      borderWidth: 1,
      borderColor: theme.borderColor,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: isDarkMode ? 0.3 : 0.05,
      shadowRadius: 4,
      elevation: 2,
    },
    cardTitle: {
      fontSize: TYPOGRAPHY.sizes.xs,
      color: theme.textSecondary,
      marginBottom: SPACING.space1,
      textTransform: 'uppercase',
      fontWeight: TYPOGRAPHY.weights.semibold,
    },
    cardValue: {
      fontSize: TYPOGRAPHY.sizes.xxl,
      fontWeight: TYPOGRAPHY.weights.bold,
      color: theme.textPrimary,
      marginBottom: SPACING.space1,
    },
    cardDesc: {
      fontSize: TYPOGRAPHY.sizes.xs,
      color: theme.textTertiary,
    },
    healthGrid: {
      marginTop: SPACING.space2,
    },
    healthRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: SPACING.space2,
      borderBottomWidth: 1,
      borderBottomColor: theme.borderColor,
    },
    healthName: {
      fontSize: TYPOGRAPHY.sizes.sm,
      color: theme.textPrimary,
    },
    indicator: {
      width: 10,
      height: 10,
      borderRadius: BORDER_RADIUS.full,
      backgroundColor: theme.success,
    },
    offlineIndicator: {
      width: 10,
      height: 10,
      borderRadius: BORDER_RADIUS.full,
      backgroundColor: theme.danger,
    }
  });

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />
      <ScrollView contentContainerStyle={styles.container}>
        
        {/* Header Block */}
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>AI-BOS Enterprise</Text>
            <Text style={styles.headerSubtitle}>Mobile Portal • Foundation v0</Text>
          </View>
          <TouchableOpacity 
            style={styles.themeBtn} 
            onPress={() => setIsDarkMode(!isDarkMode)}
            activeOpacity={0.8}
          >
            <Text style={styles.themeBtnText}>
              {isDarkMode ? '☀️ Light' : '🌙 Dark'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* System Health Metric Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>System Status</Text>
          <Text style={styles.cardValue}>Standby</Text>
          <Text style={styles.cardDesc}>Ready for container connectivity</Text>
        </View>

        {/* Multi-Agent Orchestration Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Cognitive Processing</Text>
          <Text style={styles.cardValue}>LangGraph Ready</Text>
          <Text style={styles.cardDesc}>Multi-Agent workflow engine configured</Text>
        </View>

        {/* Database Health List */}
        <View style={styles.card}>
          <Text style={[styles.cardTitle, { marginBottom: SPACING.space2 }]}>Database Connections</Text>
          
          <View style={styles.healthGrid}>
            <View style={styles.healthRow}>
              <Text style={styles.healthName}>PostgreSQL (Relational)</Text>
              <View style={styles.offlineIndicator} />
            </View>
            <View style={styles.healthRow}>
              <Text style={styles.healthName}>MongoDB (Telemetry)</Text>
              <View style={styles.offlineIndicator} />
            </View>
            <View style={styles.healthRow}>
              <Text style={styles.healthName}>Redis (Session Cache)</Text>
              <View style={styles.offlineIndicator} />
            </View>
            <View style={styles.healthRow}>
              <Text style={[styles.healthName, { borderBottomWidth: 0 }]}>Qdrant (Vector DB)</Text>
              <View style={styles.offlineIndicator} />
            </View>
          </View>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}
