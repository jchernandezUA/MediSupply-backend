#!/usr/bin/env python3
"""
Script para ejecutar el worker de procesamiento de SQS
Uso: python worker.py
"""

if __name__ == '__main__':
    from app.workers.sqs_worker import run_worker
    run_worker()
